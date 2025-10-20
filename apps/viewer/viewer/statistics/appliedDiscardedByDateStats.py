import altair as alt
import pandas as pd
import streamlit as st

from ..streamlitConn import mysqlCachedConnection


def run():
    query = """
        SELECT
            CONVERT(created, DATE) as dateCreated,
            SUM(applied) as applied,
            SUM(discarded) as discarded,
            SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview
        FROM jobs
        GROUP BY dateCreated
        ORDER BY dateCreated
    """
    df = pd.read_sql(query, mysqlCachedConnection())
    # Calcular acumulados
    df['discarded_cumulative'] = df['discarded'].cumsum()
    df['interview_cumulative'] = df['interview'].cumsum()
    # Convertir a formato largo para Altair
    df_melted = df.melt(id_vars='dateCreated',
                        value_vars=['applied', 'discarded', 'interview', 'discarded_cumulative', 'interview_cumulative'],
                        var_name='category',
                        value_name='count')
    # Renombrar categorías para mejor legibilidad
    df_melted['category'] = df_melted['category'].replace({
        'applied': 'Applied',
        'discarded': 'Discarded',
        'interview': 'Interview',
        'discarded_cumulative': 'Discarded (Σ)',
        'interview_cumulative': 'Interview (Σ)'
    })
    # Definir colores y estilos de línea
    color_scale = alt.Scale(
        domain=['Applied', 'Discarded', 'Interview',
                'Discarded (Σ)', 'Interview (Σ)'],
        range=['#0000ff', '#ff0000', '#00ff00', '#ff0000',
               '#00ff00']  # Mismos colores para acumulados
    )
    # Definir patrones de línea discontinua para los acumulados
    line_dash_scale = alt.Scale(
        domain=['Applied', 'Discarded', 'Interview', 'Discarded (Σ)', 'Interview (Σ)'],
        # Línea sólida para no acumulados, discontinua para acumulados
        range=[[], [], [], [2, 2], [2, 2]]
    )
    # Crear gráfico
    chart = alt.Chart(df_melted).mark_line().encode(
        x=alt.X('dateCreated:T', title='Date created', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('count:Q', title='Number of jobs'),
        color=alt.Color('category:N', scale=color_scale, legend=alt.Legend(title="Legend")),
        strokeDash=alt.StrokeDash('category:N', scale=line_dash_scale, legend=None),  # Estilo de línea
        tooltip=['dateCreated:T', 'category:N', 'count:Q']
    ).properties(height=800, title='Applied vs discarded jobs')
    st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":
    run()
