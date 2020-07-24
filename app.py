from flask import Flask, render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math
from datetime import datetime

with open('config.json','r') as c:
    params=json.load(c)["params"]
local_server=True

app = Flask(__name__)
app.secret_key="super-secret-key"
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']

)
mail=Mail(app)
if(local_server):
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/codingthunder'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@127.0.0.1:3307/codingthunder'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/codingthunder'
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(520), nullable=False)
    date = db.Column(db.String(120), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    tag_line=db.Column(db.String(20), nullable=True)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(2000), nullable=False)
    date = db.Column(db.String(120), nullable=True)
    img_file = db.Column(db.String(20), nullable=True)



@app.route('/')
def home():
    flash("Hii, welcome to coding thunder","success")
    flash("You can add your post here","info")
    flash("You can also edit and delete your post", "primary")
    posts = Posts.query.filter_by().all()
    last=math.ceil( len(posts)/int(params['no_of_posts']))
    #[0:params['no_of_posts']]
    #pagination
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) +int(params['no_of_posts']) ]
    #first
    if(page==1):
        prev='#'
        next='/?page=' + str(page + 1)
    elif(page==last):
        prev = '/?page=' + str(page - 1)
        next = '#'
    else:
        prev = '/?page=' + str(page - 1)
        next = '/?page=' + str(page + 1)

    return render_template('index1.html',params=params,posts=posts,prev=prev,next=next)

@app.route('/about1')
def about():
    return render_template('about1.html',params=params)

@app.route('/contact',methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        #add entry to the database

        name=request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone_num')
        message = request.form.get('message')

        entry=Contacts(name=name,email=email,phone_num=phone,message=message,date=datetime.now())

        db.session.add(entry)
        db.session.commit()

        mail.send_message('New Message From '+name, sender=email, recipients=[params['gmail-user']],
                          body=message+"\n"+phone)
        flash("Thanks for submitting your details. We will get back to you soon.","success")

    return render_template('contact.html',params=params)

@app.route('/post/<string:post_slug>', methods=['GET'])
def post(post_slug):

    post1=Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html',params=params,post=post1)

@app.route('/login',methods=['GET','POST'])
def login():

    if ('user' in session and session['user']==params['admin_user']):
        posts=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)

    if request.method=='POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')

        if(username==params['admin_user'] and userpass==params['admin_password']):
            session['user']=username   #set the session variable
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)

    return render_template('login.html',params=params)

@app.route('/edit/<string:sno>',methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            title=request.form.get('title')
            tline=request.form.get('tline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()

            if sno=='0':
                post=Posts(title=title,tag_line=tline,slug=slug,content=content,date=date,img_file=img_file)
                db.session.add(post)
                db.session.commit()

            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=title
                post.tag_line=tline
                post.slug=slug
                post.content=content
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)

@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f=request.files['file1']
            #print(os.path.join(app.config['UPLOAD_FOLDER']),secure_filename(f.filename))
            #f.save((app.config['UPLOAD_FOLDER'])+'\\'+ secure_filename(f.filename))
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')

@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')


app.run(debug=True)