from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from sonnet import app, bcrypt, db
from sonnet.forms import PostForm, LoginForm, RegistrationForm, UpdateAccountForm,SearchForm,AddCommentForm
from sonnet.models import Post, Tag, User, Comment
import os
from PIL import Image
import re
import secrets


@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page=page, per_page=5)
    # posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    contents = []
    for post in posts.items:
        contents.append(process_content(post.content))
    return render_template('home.html', posts=posts, contents=contents)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Login to continue.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check the credentials.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('search'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pictures', picture_fn)
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename=f'profile_pictures/{current_user.image_file}')
    return render_template('account.html', title='Account', image_file=image_file, form=form)

def save_track(form_track):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_track.filename)
    track_fn = random_hex + f_ext
    track_path = os.path.join(app.root_path, 'static/tracks', track_fn)
    form_track.save(track_path)
    return track_fn

def process_tags(text):
    tags = re.findall('#[\w]*', text)
    normalised = []
    if tags:
        for tag in tags:
            tg_eff = tag.lower()[1:]
            tg = Tag.query.filter_by(name=tg_eff).first()
            if tg is None:
                tg = Tag(name=tg_eff)
            normalised.append(tg)
    return normalised

def process_content(text):
    tags = re.findall('#[\w]*', text)
    if tags:
        for tag in tags:
            t = url_for('topic', tag=tag.lower()[1:])
            text = text.replace(tag, f'<a href="{t}">{tag}</a>')
    return text

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        track_file = save_track(form.track.data)
        tags = process_tags(form.content.data)
        for tag in tags:
            tg_ex = Tag.query.filter_by(name=tag.name).first()
            if tg_ex is None:
                db.session.add(tag)
        post = Post(title=form.title.data, content=form.content.data, track=track_file, author=current_user, tags=tags)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('edit_post.html', title='New Post', legend='New Post', form=form)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    content = process_content(post.content)
    form = AddCommentForm()
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.desc()).all()   #.order_by(Post.date_posted.desc())
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post_id=post.id, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been added to the post", "success")
        return redirect(url_for("post", post_id=post.id))
    return render_template('post.html', title=post.title, content=content, post=post, form= form, comments= comments)

@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.track.data:
            track_file = save_track(form.track.data)
            post.track = track_file
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('update_post.html', title='Update Post', legend='Update Post', form=form)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/user/<string:username>')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    contents = []
    for post in posts.items:
        contents.append(process_content(post.content))
    return render_template('user_posts.html',posts=posts, contents=contents, user=user)

@app.route('/topic/<string:tag>')
def topic(tag):
    tag = Tag.query.filter_by(name=tag.lower()).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = tag.posts.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    contents = []
    for post in posts.items:
        contents.append(process_content(post.content))
    return render_template('topic.html', title=tag.name, posts=posts, contents=contents, tag=tag)

@app.route('/home/<int:post_id>/<action>')
@login_required
def like_action(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'like':
        current_user.like(post)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike(post)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/home/<type>/<int:user_id>/<action>')
@login_required
def follow_action(type,user_id, action):
    user = User.query.filter_by(id=user_id).first_or_404()
    if action == 'follow':
        current_user.follow(user)
        db.session.commit()
    if action == 'unfollow':
        current_user.unfollow(user)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/')
@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    searches=[]
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    contents = []
    for post in posts.items:
        contents.append(process_content(post.content))
    
    tagposts=[]
    tagcontents=[]
    if form.validate_on_submit():
        search_value=form.search.data
        search = "%{0}%".format(search_value)
        usersresult = User.query.filter(User.username.like(search)).all()
        tagsresult = Tag.query.filter(Tag.name.like(search.lower())).all()
        searches=usersresult
        print(tagsresult)
        for tag in tagsresult:
            print(tag)
            posts = tag.posts.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
            tcontents = []
            tposts =[]
            for post in posts.items:
                tposts.append(post)
                tcontents.append(process_content(post.content))
            tagposts.extend(tposts)
            tagcontents.extend(tcontents)
    return render_template('search.html', title='Search', form=form, result=searches,tagposts=tagposts,tagcontents=tagcontents ,posts=posts, contents=contents)