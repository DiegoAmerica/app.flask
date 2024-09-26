import streamlit as st
import pandas as pd
import numpy as np
import openpyxl
import plotly.graph_objects as go

class Estudoprodutootimo():
    def __init__(self, dados, flexmin, flexmax, sazo, tiposazo):
        self.dados = dados
        self.flexmin =  flexmin
        self.flexmax = flexmax
        self.sazo = sazo
        self.tiposazo = tiposazo

    def df(self):
        dados = self.dados
        return dados

    def flex_min(self):
        flex = self.flexmin
        return flex

    def flex_max(self):
        flex = self.flexmax
        return flex

    def input_sazo(self):
        sazo = self.sazo
        return sazo

    def tipo_sazo(self):
        tipo = self.tiposazo
        return tipo

    def maxima_consumo(self):
        dados_processados = self.df()
        consumo = pd.DataFrame(dados_processados.loc[[0,1,2,3]].max(axis=0) * (1+0.05)).T
        return consumo

    def volume_mwm(self):
        dados_consumo = self.df()
        consumo_maximo = self.maxima_consumo()
        data = pd.DataFrame({'Consumo': consumo_maximo.iloc[0], 'horas': dados_consumo.iloc[4]}).T
        consumo = data.iloc[0]
        horas = data.iloc[1]
        div = np.divide(consumo, horas)
        div = pd.DataFrame(div).T
        return div

    def inclusao_desvio_mes(self):
        consumo_maximo = self.maxima_consumo()
        dados_consumo = self.df()
        mwm = self.volume_mwm()
        data = pd.DataFrame({'Consumo': consumo_maximo.iloc[0], 'horas': dados_consumo.iloc[4], 'volume mwm': mwm.iloc[0]}).T
        total_MWh = np.sum(data.iloc[0])
        total_horas = np.sum(data.iloc[1])
        total_mwm = np.divide(total_MWh, total_horas)
        volume_mwm_mes = data.iloc[2]
        desvio = np.divide(volume_mwm_mes, total_mwm)-1
        desvio = pd.DataFrame(desvio).T
        return desvio

    def maxima_variacao(self):
        max = self.inclusao_desvio_mes()
        max = pd.DataFrame({'maximo desvio':max.iloc[0]}).abs().max().T
        return max

    def relacao_sazo(self):
        varicao = self.maxima_variacao()
        sazo = self.input_sazo()
        ralacao = varicao/sazo
        return ralacao

    def desvio_normalizado(self):
        relacao = self.relacao_sazo()
        desvio = self.inclusao_desvio_mes()
        data = pd.DataFrame({'relacao':relacao.iloc[0], 'desvio': desvio.iloc[0]}).T
        desvio = data.iloc[1]
        relacao = data.iloc[0]
        normal = pd.DataFrame(np.divide(desvio, relacao)).T
        return normal

    def contrato_ajustado_mwm(self):
        sazo = self.tipo_sazo()
        consumo_maximo = self.maxima_consumo()
        desvio = self.desvio_normalizado()
        dados_consumo = self.df()
        data = pd.DataFrame({'volume':consumo_maximo.iloc[0], 'desvio': desvio.iloc[0], 'horas': dados_consumo.iloc[4]}).T
        volume = np.sum(data.iloc[0])
        desvio = data.iloc[1]
        horas = np.sum(data.iloc[2])
        volume_total = np.divide(volume, horas)
        contrato_ajustado = pd.DataFrame(np.multiply(volume_total, (1+desvio))).T
        data_mwm = pd.DataFrame({f'coluna{i}': [volume_total] for i in range(1,13)})
        novos_nomes = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        data_mwm.columns = novos_nomes
        data_mwm = data_mwm.iloc[0]
        if sazo == 'PORCENTAGEM':
            return contrato_ajustado
        else:
            return data_mwm

    def contrato_ajutado_mwh(self):
        volume_ajustado = self.contrato_ajustado_mwm()
        dados_consumo = self.df()
        data = pd.DataFrame({'volume mwm': volume_ajustado.iloc[0], 'horas': dados_consumo.iloc[4]}).T
        volume_mwm = data.iloc[0]
        horas = data.iloc[1]
        contrato_ajustado_mwh = pd.DataFrame(np.multiply(volume_mwm, horas)).T
        return contrato_ajustado_mwh

    def desvio_flex_max(self):
        desvio_consumo = self.data_desvio_consumo()
        flex = self.flex_max()
        desvio_consumo = pd.DataFrame({'sazo sugerida': desvio_consumo.iloc[12]})
        flex = pd.DataFrame(np.multiply(desvio_consumo, (1+flex))).T
        return flex

    def desvio_flex_min(self):
        desvio_consumo = self.data_desvio_consumo()
        flex = self.flex_min()
        desvio_consumo = pd.DataFrame({'sazo sugerida': desvio_consumo.iloc[12]})
        flex = pd.DataFrame(np.multiply(desvio_consumo, (1-flex))).T
        return flex

    def necessidade(self):
        consumo = self.maxima_consumo()
        com_perdas = pd.DataFrame(consumo.iloc[0]*(1+0.03)).T
        return com_perdas

    def take(self):
        medicao_perdas = self.necessidade()
        flex_max = self.desvio_flex_max()
        flex_min = self.desvio_flex_min()

        data = pd.DataFrame({'Necessidade': medicao_perdas.iloc[0], 'flex max': flex_max.iloc[0], 'flex min': flex_min.iloc[0]}).T

        result = pd.Series(index=data.index)
        indices_para_remover = ['Necessidade','flex max', 'flex min']
        result = pd.DataFrame(result.drop(indices_para_remover)).T

        for coluna in data.columns:
            necessidade1 = data.loc['Necessidade', coluna]
            flex_max1 = data.loc['flex max', coluna]
            flex_min1 = data.loc['flex min', coluna]

            if (necessidade1 > flex_max1).all():
                result[coluna] = flex_max1
            elif (necessidade1 < flex_min1).all():
                result[coluna] = flex_min1
            elif (necessidade1 > flex_min1).all() and (necessidade1 < flex_max1).all():
                result[coluna] = necessidade1
            else:
                result[coluna] = None
        return result

    def exposicao(self):
        faturar = self.take()
        necessario = self.necessidade()
        expos = np.subtract(faturar, necessario)
        expos = pd.DataFrame(expos)
        return expos

    def variacao_take(self):
        faturar = self.take()
        exposi = self.exposicao()
        variacao = np.divide(exposi, faturar)
        variacao = pd.DataFrame(variacao)
        return variacao

    def meses(self):
        meses = pd.DataFrame({'Meses':['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']}).T
        return meses

    def data_desvio_consumo(self):
        dados_consumo = self.df()
        consumo_maximo = self.maxima_consumo()
        consumo_medio = self.volume_mwm()
        desvio_mes = self.inclusao_desvio_mes()
        maxima_variacao_desvio = self.maxima_variacao()
        sazo = self.relacao_sazo()
        normalizado = self.desvio_normalizado()
        ajustado_mwm = self.contrato_ajustado_mwm()
        ajustado_mwh = self.contrato_ajutado_mwh()

        data = pd.DataFrame({'Ano 1':dados_consumo.iloc[0],
                            'Ano 2':dados_consumo.iloc[1],
                            'Ano 3':dados_consumo.iloc[2],
                            'Ano 4':dados_consumo.iloc[3],
                            'Horas [h]':dados_consumo.iloc[4],
                            'Consumo Máximo [MWh]':consumo_maximo.iloc[0], 
                            'Consumo Médio [MWm]':consumo_medio.iloc[0],
                            'Desvio Consumo (% Variação)':desvio_mes.iloc[0],
                            'Máxima Variação (%)':maxima_variacao_desvio.iloc[0],
                            'Relação Sazo (%)':sazo.iloc[0],
                            'Desvio Consumo Normalizado (% Variação)':normalizado.iloc[0],
                            'Contrato Ajustado (MWm)':ajustado_mwm.iloc[0],
                            'Contrato Ajustado (MWh)': ajustado_mwh.iloc[0]
        }).T

        return data

    def data_desvio_take(self):
        flex_max = self.desvio_flex_max()
        desvio_consumo = self.data_desvio_consumo()
        flex_min = self.desvio_flex_min()
        onecessario = self.necessidade()
        calc_take = self.take()
        exposi = self.exposicao()
        variacao = self.variacao_take()

        data = pd.DataFrame({'Flex Máx. [MWh]': flex_max.iloc[0], 
                            'Sazo Sugerida [MWh]':desvio_consumo.iloc[12],
                            'Flex Min. [MWh]': flex_min.iloc[0],
                            'Sazo Sugerida [MWm]':desvio_consumo.iloc[11],
                            'Necessidade [MWh]': onecessario.iloc[0],
                            'Take [MWh]': calc_take.iloc[0],
                            'Exposição [MWh]':exposi.iloc[0],
                            'Variação Exposição / Take [%]':variacao.iloc[0]
        }).T
    
        return data

    def grafico(self):
        take = self.data_desvio_take()
        data_meses = self.meses()

        fig = go.Figure(layout=dict(width=1500, height=500))
        fig.add_trace(go.Bar(x=data_meses.loc['Meses'], y=take.loc['Necessidade [MWh]'], name='Necessidade [MWh]', marker_color='orange'))
        fig.add_trace(go.Bar(x=data_meses.loc['Meses'], y=take.loc['Take [MWh]'], name='Take [MWh]', marker_color='blue'))
        fig.add_trace(go.Scatter(x=data_meses.loc['Meses'], y=take.loc['Flex Máx. [MWh]'], mode='lines+markers', name='Flex Máx. [MWh]', line=dict(color='red', width=2)))
        fig.add_trace(go.Scatter(x=data_meses.loc['Meses'], y=take.loc['Flex Min. [MWh]'], mode='lines+markers', name='Flex Min. [MWh]', line=dict(color='red', width=2)))
        fig.add_trace(go.Scatter(x=data_meses.loc['Meses'], y=take.loc['Sazo Sugerida [MWh]'], mode='lines+markers', name='Sazo Sugerida [MWh]', line=dict(color='green', width=2)))
        fig.update_layout(title='Previsão - Balanço Energético (MWh)', xaxis_title='Meses', yaxis_title='Contrato Ajustado [MWh]')
        return fig

