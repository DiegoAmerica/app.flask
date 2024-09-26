from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import plotly.graph_objects as go
from desvio_consumo import Estudoprodutootimo

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            dados = pd.read_excel(file, sheet_name='dados_consumo')
            dados_json = dados.to_json()
            return redirect(url_for('definicao_produto', dados=dados_json))
    return render_template('upload.html')

@app.route('/definicao_produto', methods=['GET'])
def definicao_produto():
    dados = request.args.get('dados')
    return render_template('definicao_produto.html', dados=dados)

@app.route('/otimo', methods=['GET'])
def otimo():
    dados = pd.read_json(request.args.get('dados'))
    date = Estudoprodutootimo(dados, 0, 0, 0, "PORCENTAGEM")
    desvio_consumo = date.data_desvio_consumo()
    desvio_take = date.data_desvio_take()
    max_varaiçãop1 = round(date.maxima_variacao(), 2)
    max_varaiçãop = round(date.maxima_variacao() * 100, 2)
    max_varaiçãop = sum(max_varaiçãop)
    max_varaiçãop_str = f"{max_varaiçãop}%"
    total_MWh = round(desvio_consumo.iloc[5].mean(), 3)
    total_MWm = round(desvio_consumo.iloc[6].mean(), 3)
    flexmax = round(desvio_take.iloc[7].max(), 3)
    flexmaxp = f"{round(flexmax * 100, 3)}%"
    date1 = Estudoprodutootimo(dados, flexmax, flexmax, max_varaiçãop1, "PORCENTAGEM")
    desvio_consumo1 = date1.data_desvio_consumo()
    desvio_take1 = date1.data_desvio_take()

    fig = date1.grafico()
    graph_html = fig.to_html(full_html=False)

    return render_template('otimo.html', desvio_consumo=desvio_consumo1.to_html(), desvio_take=desvio_take1.to_html(), max_varaiçãop=max_varaiçãop_str, total_MWh=total_MWh, total_MWm=total_MWm, flexmax=flexmaxp, graph_html=graph_html, dados=request.args.get('dados'))

@app.route('/ajustado', methods=['GET', 'POST'])
def ajustado():
    if request.method == 'POST':
        dados = pd.read_json(request.form['dados'])
        flexmin = float(request.form['flexmin']) / 100
        flexmax = float(request.form['flexmax']) / 100
        sazo = float(request.form['sazo']) / 100
        tiposazo = request.form['tiposazo']
        date = Estudoprodutootimo(dados, flexmin, flexmax, sazo, tiposazo)
        desvio_consumo = date.data_desvio_consumo()
        desvio_take = date.data_desvio_take()
        max_varaiçãop = round(date.maxima_variacao() * 100, 2)
        max_varaiçãop = sum(max_varaiçãop)
        max_varaiçãop_str = f"{max_varaiçãop}%"
        total_MWh = round(desvio_consumo.iloc[5].mean(), 3)
        total_MWm = round(desvio_consumo.iloc[6].mean(), 3)
        flexmax = round(desvio_take.iloc[7].max(), 3)
        flexmaxp = f"{round(flexmax * 100, 3)}%"
        fig = date.grafico()
        graph_html = fig.to_html(full_html=False)

        return render_template('ajustado.html', desvio_consumo=desvio_consumo.to_html(), desvio_take=desvio_take.to_html(), max_varaiçãop=max_varaiçãop_str, total_MWh=total_MWh, total_MWm=total_MWm, flexmax=flexmaxp, graph_html=graph_html, dados=request.form['dados'])
    else:
        dados = request.args.get('dados')
        return render_template('ajustado.html', dados=dados)

if __name__ == '__main__':
    app.run(debug=True)