from flask import request, render_template, Blueprint, send_file, url_for, redirect
import requests
import os
import json
import pandas as pd
from datetime import datetime
from cache import cache

tloapp = Blueprint('tloapp',__name__)

@tloapp.route('/', methods=['GET'])
def loadhomepage():
    product_model_list = cache.get("menu_list")
    if product_model_list is None:
        print("CACHE NOT EXIST")
        response = requests.get(f'{os.environ.get("API_ENDPOINT")}/api/products')
        payload = response.json()
        product_item = payload['payload']
        product_model_list = []
        for each in product_item:
            items = {}
            items['product_name'] = each['name']
            items['product_id'] = each['id']
            response = requests.get(f'{os.environ.get("API_ENDPOINT")}/api/models/{items["product_id"]}')
            items['model_list'] = response.json()['payload']
            product_model_list.append(items)
        cache.set("menu_list",product_model_list)
    else :
        print("CACHE USED")
        # product_model_list = cache.get("menu_list")
    return render_template('tloML/home.html', product_model_list=product_model_list)

@tloapp.route('/product/<product_id>/model/<model_id>', methods=['GET','POST'])
@cache.cached()
def loadmodelpage(product_id, model_id):
    print("Cache Not Exist")
    response = requests.get(f"{os.environ.get('API_ENDPOINT')}/api/models/{product_id}")
    models_info = json.loads(response.text)
    found_flag = False
    for each in models_info['payload']:
        if each['id'] == model_id:
            found_flag = True
            model_category = each['model_type']
            model_name = each['model_name']
            model_desc = each['desc']

    if found_flag is False:
        return "model not found"

    if model_category == "Text_Classification":
        if request.method == 'POST':
            item_name = request.form['item_name']
            item_list = [item_name]
            if item_name:
                payload = json.dumps({
                "item_list" : item_list
                })
                # print(payload)
                response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/model/{model_id}/classify", headers={"Content-Type": "application/json"}, data=payload)
                # print(response.status_code)
                # print(response.text)
                # print(response.headers)
                item = response.json()['item_list']
                # print(item[0]['item_name'])
                return render_template('modelUI/item_clf_run.html', model_id=model_id, item_name = item[0]['item_name'], item_category = item[0]['classified_category'])
            else:
                f = request.files['csvFile']
                f.save('itemlist2classify.csv')
                itemdf = pd.read_csv(r'./itemlist2classify.csv')
                item_list = itemdf['item_name'].tolist()
                payload = json.dumps({
                "item_list" : item_list
                })
                response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/model/{model_id}/classify", headers={"Content-Type": "application/json"}, data=payload)
                item = response.json()['item_list']
                categorized_item_list = []
                for each in item:
                    row = []
                    item_name = each['item_name']
                    item_category = each['classified_category']
                    row = [item_name,item_category]
                    categorized_item_list.append(row)
                categorized_item_df = pd.DataFrame(data=categorized_item_list,columns=["item_name","categorized_item"])
                categorized_item_df.to_csv('./itemlistclassified.csv')
                # return url_for('tloapp.displayreportpage', product_id=product_id, model_id=model_id)
                return render_template('modelUI/classify_report.html', data=categorized_item_list[:50], product_id=product_id, model_id=model_id)
        else:
            return render_template('modelUI/item_clf_run.html', product_id=product_id, model_id=model_id)
    elif model_category=="Time_Forcasting": 
        forcast_data = cache.get("forcast_data")
        if forcast_data is None:
            print("forecast CACHE NOT EXIST")
            response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/model/{model_id}/predict")
            predictions = json.loads(response.text)
            labels = []
            data = []
            for each in predictions['forcast']:
                labels.append(each['date'])
                data.append(each['prediction'])
            forcast_data = {
                "data" : data,
                "error_metrics" : predictions["RMSE"],
                "last_update" : predictions['forcast_datetime'],
                "labels" : labels,
                "model_name" : model_name,
                "model_desc" : model_desc
            }
            cache.set("forcast_data", forcast_data)
            return render_template('modelUI/time_forcast.html', data=data, error_metrics=predictions['RMSE'], last_update=predictions['forcast_datetime'], labels=labels, product_id=product_id, model_id=model_id, model_name=model_name, model_desc=model_desc, cache_key="forcast_data")
        else:
            print("Forcast Cache USED!")
            return render_template('modelUI/time_forcast.html', data=forcast_data["data"], error_metrics=forcast_data['error_metrics'], last_update=forcast_data['last_update'], labels=forcast_data['labels'], product_id=product_id, model_id=model_id, model_name=forcast_data['model_name'], model_desc=forcast_data['model_desc'], cache_key="forcast_data")
    else:
        return "model type unsupported"

@tloapp.route('/product/<product_id>/model/<model_id>&force_update=True?cache_key=<cache_key>', methods=['GET','POST'])
def force_update(product_id, model_id, cache_key):
    cache.delete(cache_key)
    print("FORCE UPDATED")
    # cache.delete(f"view/{str(url_for('tloapp.loadmodelpage', product_id = product_id, model_id = model_id))}")
    return redirect(url_for('tloapp.loadmodelpage', product_id = product_id, model_id = model_id))

@tloapp.route('/product/<product_id>/model/<model_id>/report', methods=['GET','POST'])
def displayreportpage(product_id,model_id):
    if request.method=="POST":
        if request.form['submit_button'] == "download" :
           return send_file('./itemlistclassified.csv',
                     mimetype='text/csv',
                     attachment_filename='itemlistclassified.csv',
                     as_attachment=True)
    return render_template('modelUI/classify_report.html', model_id=model_id, product_id=product_id)

@tloapp.route('/product/<product_id>/manage', methods=['GET','POST'])
def manageproductpage(product_id):
    if request.method=='POST':
        if request.form['submit_button'] == "submit":
            product_name = request.form['product_name']
            product_desc = request.form['product_desc']
            payload = json.dumps({
                "product_name" : product_name,
                "desc" : product_desc
                })
            response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/product/add", headers={"Content-Type": "application/json"}, data=payload)
            return render_template('tloML/home.html')
        elif request.form['submit_button'] == "edit":
            product_name = request.form['product_name']
            product_desc = request.form['product_desc']
            payload = json.dumps({
                "product_name" : product_name,
                "desc" : product_desc
                })
            response = requests.put(f"{os.environ.get('API_ENDPOINT')}/api/product/{product_id}", headers={"Content-Type": "application/json"}, data=payload)
            return render_template('tloML/home.html')
        elif request.form['submit_button'] == "delete":
            response = requests.delete(f"{os.environ.get('API_ENDPOINT')}/api/product/{product_id}", headers={"Content-Type": "application/json"})
            return render_template('tloML/home.html')
        else :
            return render_template('tloML/home.html')
    if str(product_id).lower() != 'new':
        response = requests.get(f'{os.environ.get("API_ENDPOINT")}/api/products')
        payload = response.json()['payload']
        match_product_name = ""
        match_product_desc = ""
        for each in payload:
            if each['id'] == product_id:
                match_product_name = each['name']
                match_product_desc = each['desc']
        return render_template('tloML/product.html', product_id=product_id, product_name=match_product_name, product_desc=match_product_desc)
        # response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/product/{product_id}", headers={"Content-Type": "application/json"})
    return render_template('tloML/product.html', product_id=product_id)

@tloapp.route('/product/<product_id>/model/<model_id>/manage', methods=['GET','POST'])
def managemodelpage(product_id,model_id):
    if request.method=='POST':
        if request.form['submit_button'] == "submit":
            model_name = request.form['model_name']
            model_desc = request.form['model_desc']
            payload = json.dumps({
                "model_name_name" : model_name,
                "desc" : model_desc
                })
            # response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/product/add", headers={"Content-Type": "application/json"}, data=payload)
            return render_template('tloML/home.html')
        elif request.form['submit_button'] == "edit":
            model_name = request.form['model_name']
            model_desc = request.form['model_desc']
            payload = json.dumps({
                "model_name" : model_name,
                "desc" : model_desc
                })
            # response = requests.put(f"{os.environ.get('API_ENDPOINT')}/api/product/{product_id}", headers={"Content-Type": "application/json"}, data=payload)
            return render_template('tloML/home.html')
        elif request.form['submit_button'] == "delete":
            response = requests.delete(f"{os.environ.get('API_ENDPOINT')}/api/product/{product_id}", headers={"Content-Type": "application/json"})
            return render_template('tloML/home.html')
        else :
            return render_template('tloML/home.html')
    if str(model_id).lower() != 'new':
        response = requests.get(f'{os.environ.get("API_ENDPOINT")}/api/products')
        payload = response.json()['payload']
        match_model_name = ""
        match_model_desc = ""
        for each in payload:
            if each['id'] == model_id:
                match_model_name = each['name']
                match_model_desc = each['desc']
        return render_template('tloML/model.html', model_id=model_id, model_name=match_model_name, model_desc=match_model_desc)
        # response = requests.post(f"{os.environ.get('API_ENDPOINT')}/api/product/{model_id}", headers={"Content-Type": "application/json"})
    return render_template('tloML/model.html', model_id=model_id)

