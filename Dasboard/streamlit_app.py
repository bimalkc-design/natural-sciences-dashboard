import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import date
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title='Natural Sciences Dashboard',layout='wide')
DB='data/natural_sciences.db'
PROGRAMMES=['Life Science','Chemistry','Physics']

conn=sqlite3.connect(DB,check_same_thread=False)
cur=conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS performance(id INTEGER PRIMARY KEY, programme TEXT, academic_year TEXT, category TEXT, students INTEGER)')
cur.execute('CREATE TABLE IF NOT EXISTS employment(id INTEGER PRIMARY KEY, programme TEXT, student_id TEXT,name TEXT,gender TEXT,status TEXT,organization TEXT,remarks TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS exchange_prog(id INTEGER PRIMARY KEY, year TEXT, programme TEXT, student TEXT,institution TEXT,country TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS internship(id INTEGER PRIMARY KEY, year TEXT, programme TEXT, student TEXT,organization TEXT,location TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS guest(id INTEGER PRIMARY KEY, lecture_date TEXT,speaker TEXT,institution TEXT,topic TEXT,programme TEXT)')
conn.commit()

st.title('Natural Sciences Department Dashboard')
menu=st.sidebar.radio('Module',['Dashboard','Performance','Employment','Exchange','Internships','Guest Lectures'])

def q(tbl): return pd.read_sql_query(f'select * from {tbl}',conn)

if menu=='Dashboard':
    p,e,x,i,g=[q(t) for t in ['performance','employment','exchange_prog','internship','guest']]
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric('Performance Records',len(p))
    c2.metric('Employment Records',len(e))
    c3.metric('Exchange Records',len(x))
    c4.metric('Internships',len(i))
    c5.metric('Guest Lectures',len(g))
    if not p.empty:
        fig=px.bar(p.groupby(['programme','category'])['students'].sum().reset_index(),x='programme',y='students',color='category',title='Student Performance')
        st.plotly_chart(fig,use_container_width=True)

elif menu=='Performance':
    st.subheader('Add Student Performance')
    with st.form('perf'):
        prog=st.selectbox('Programme',PROGRAMMES)
        yr=st.selectbox('Academic Year',['Year 1','Year 2','Year 3'])
        cat=st.selectbox('Category',['Outstanding','Very Good','Good','Satisfactory','Failed','Re-Assessment'])
        stu=st.number_input('Students',0,1000,1)
        if st.form_submit_button('Save'):
            cur.execute('insert into performance(programme,academic_year,category,students) values (?,?,?,?)',(prog,yr,cat,stu));conn.commit();st.success('Saved')
    df=q('performance'); st.data_editor(df,use_container_width=True)

elif menu=='Employment':
    with st.form('emp'):
        p=st.selectbox('Programme',PROGRAMMES)
        sid=st.text_input('Student ID')
        nm=st.text_input('Name')
        g=st.selectbox('Gender',['Male','Female'])
        s=st.selectbox('Status',['Employed','Higher Studies','Unemployed','Self Employed','Internship'])
        o=st.text_input('Organization/Institution')
        r=st.text_input('Remarks')
        if st.form_submit_button('Save'):
            cur.execute('insert into employment(programme,student_id,name,gender,status,organization,remarks) values (?,?,?,?,?,?,?)',(p,sid,nm,g,s,o,r));conn.commit();st.success('Saved')
    st.dataframe(q('employment'),use_container_width=True)

elif menu=='Exchange':
    with st.form('ex'):
        y=st.text_input('Year',str(date.today().year))
        p=st.selectbox('Programme',PROGRAMMES)
        s=st.text_input('Student')
        ins=st.text_input('Institution')
        c=st.text_input('Country')
        if st.form_submit_button('Save'):
            cur.execute('insert into exchange_prog(year,programme,student,institution,country) values (?,?,?,?,?)',(y,p,s,ins,c));conn.commit();st.success('Saved')
    st.dataframe(q('exchange_prog'),use_container_width=True)

elif menu=='Internships':
    with st.form('int'):
        y=st.text_input('Year')
        p=st.selectbox('Programme',PROGRAMMES)
        s=st.text_input('Student')
        o=st.text_input('Organization')
        l=st.text_input('Location')
        if st.form_submit_button('Save'):
            cur.execute('insert into internship(year,programme,student,organization,location) values (?,?,?,?,?)',(y,p,s,o,l));conn.commit();st.success('Saved')
    st.dataframe(q('internship'),use_container_width=True)

elif menu=='Guest Lectures':
    with st.form('guest'):
        d=st.date_input('Date')
        sp=st.text_input('Speaker')
        ins=st.text_input('Institution')
        t=st.text_input('Topic')
        p=st.selectbox('Programme',PROGRAMMES)
        if st.form_submit_button('Save'):
            cur.execute('insert into guest(lecture_date,speaker,institution,topic,programme) values (?,?,?,?,?)',(str(d),sp,ins,t,p));conn.commit();st.success('Saved')
    st.dataframe(q('guest'),use_container_width=True)

st.sidebar.markdown('### Export')
if st.sidebar.button('Export Excel'):
    out=BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as w:
        q('performance').to_excel(w,'Performance',index=False)
        q('employment').to_excel(w,'Employment',index=False)
        q('exchange_prog').to_excel(w,'Exchange',index=False)
        q('internship').to_excel(w,'Internships',index=False)
        q('guest').to_excel(w,'GuestLectures',index=False)
    st.sidebar.download_button('Download Workbook',out.getvalue(),'Natural_Sciences_Dashboard.xlsx')
