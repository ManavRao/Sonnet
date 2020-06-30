
from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from sonnet import app, bcrypt, db
from sonnet.forms import PostForm, LoginForm, RegistrationForm, UpdateAccountForm, SearchForm, AddCommentForm, PostUpdateForm
from sonnet.models import Post, Tag, User, Comment
import os
from PIL import Image
import re
import secrets

# route for home page
@app.route('/home')
def home():
    # the home page is paginated and hence handling page query
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page=page, per_page=5)
    contents = []
    num_comments=[]
    # processing each post to be displayed on the page
    for post in posts.items:
        contents.append(process_content(post.content))
        num_comment = len(Comment.query.filter_by(post_id=post.id).all())
        num_comments.append(num_comment)
    return render_template('home.html', posts=posts, contents=contents, num_comments=num_comments)

# route for about page
@app.route('/about')
def about():
    return render_template('about.html', title='About')

# route for register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()   #pulling registraion form from forms.py
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  #password is hashed for privacy reasons
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Login to continue.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()  #pulling login form from forms.py
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check the credentials.', 'danger')     #handling the alternate path of unsuccessful login
    return render_template('login.html', title='Login', form=form)

#route for logout page
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('search'))

# helper function to crop image with center as image center
def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))

# helper function to crop the image into square of maximum possible size from input image
def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))

# helper function to save image to desired size
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pictures', picture_fn)
    output_size = (150, 150)
    i = Image.open(form_picture)
    i = crop_max_square(i).resize(output_size, Image.LANCZOS)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


# route for user account access
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm() #pulling account form from forms.py
    if form.validate_on_submit():
        # if picture is added, processing picture
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            if current_user.image_file != 'default.jpg':
                os.remove(os.path.join(app.root_path, 'static/profile_pictures', current_user.image_file))
            current_user.image_file = picture_file
        current_user.username = form.username.data  #username update
        current_user.email = form.email.data    #email update
        db.session.commit()
        flash('Account updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename=f'profile_pictures/{current_user.image_file}')
    return render_template('account.html', title='Account', image_file=image_file, form=form)

#helper function to save audio track for the post
def save_track(form_track):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_track.filename)
    track_fn = random_hex + f_ext
    track_path = os.path.join(app.root_path, 'static/tracks', track_fn)
    form_track.save(track_path)
    return track_fn

#helper function to process the tags and convert them to html links
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

# helper fucntion to extract tags from the post content
def process_content(text):
    tags = re.findall('#[\w]*', text)
    idx = -1
    if tags:
        for tag in tags:
            t = url_for('topic', tag=tag.lower()[1:])
            text = text[:idx+1] + text[idx+1:].replace(tag, f'<a href="{t}">{tag}</a>', 1)
            idx = text.index(tag)
    return text

# route for a new post upload
@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm() #pulling post form from forms.py
    if form.validate_on_submit():
        track_file = save_track(form.track.data)
        tags = process_tags(form.content.data)
        # if hashtags are found they are processed to be displayed as links
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

# route for accessing an existing post
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    content = process_content(post.content)
    form = AddCommentForm() #pulling comments form from forms.py
    # comments are shown in first come first see order
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.asc()).all()
    # if comment is added it is processed and added to the database, basic commenting feature
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post_id=post.id, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been added to the post", "success")
        return redirect(url_for("post", post_id=post.id))
    num_comment = len(comments)
    print(num_comment)
    return render_template('post.html', title=post.title, content=content, post=post, form= form, comments= comments, num_comment= num_comment)

# route for updating a post
@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostUpdateForm() #pulling post update form from forms.py
    if form.validate_on_submit():
        # if track is updated, old one is removed and new is stored into the databse
        if form.track.data:
            os.remove(os.path.join(app.root_path, 'static/tracks', post.track))
            track_file = save_track(form.track.data)
            post.track = track_file
        # processing the content and hashtags
        tags = process_tags(form.content.data)
        for tag in tags:
            tg_ex = Tag.query.filter_by(name=tag.name).first()
            if tg_ex is None:
                db.session.add(tag)
        post.tags = tags
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('update_post.html', title='Update Post', legend='Update Post', form=form)

# route for deleting a post
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    os.remove(os.path.join(app.root_path, 'static/tracks', post.track))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

# route for seeing all posts of a user
@app.route('/user/<string:username>')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    contents = []
    num_comments=[]
    for post in posts.items:
        contents.append(process_content(post.content))
        num_comment = len(Comment.query.filter_by(post_id=post.id).all())
        num_comments.append(num_comment)
    print(num_comments)
    return render_template('user_posts.html',posts=posts, contents=contents, user=user, num_comments=num_comments)

# route for seeing all posts corresponding to a particluar hashtag
@app.route('/topic/<string:tag>')
def topic(tag):
    tag = Tag.query.filter_by(name=tag.lower()).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = tag.posts.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    contents = []
    num_comments=[]
    for post in posts.items:
        contents.append(process_content(post.content))
        num_comment = len(Comment.query.filter_by(post_id=post.id).all())
        num_comments.append(num_comment)
    return render_template('topic.html', title=tag.name, posts=posts, contents=contents, tag=tag, num_comments=num_comments)

# route for liking and disliking
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

# route for following
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

# route for search page, the main explore page
@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    searches=[]
    page = request.args.get('page', 1, type=int)
    explore_posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5,error_out=False)
    contents = []
    num_comments=[]

    for post in explore_posts.items:
        contents.append(process_content(post.content))
        num_comment = len(Comment.query.filter_by(post_id=post.id).all())
        num_comments.append(num_comment)

    tagposts=[]
    tagcontents=[]
    tagnum_comments=[]
    if form.validate_on_submit():
        search_value=form.search.data
        search = "%{0}%".format(search_value)
        usersresult = User.query.filter(User.username.like(search)).all()
        tagsresult = Tag.query.filter(Tag.name.like(search.lower())).all()
        searches = usersresult
        tagpostset = set()
        for tag in tagsresult:
            posts = tag.posts.order_by(Post.date_posted.desc())
            tcontents = []
            tnum_comments=[]
            tposts =[]
            for post in posts:
                if(post.id in tagpostset):
                    continue

                tagpostset.add(post.id)
                tposts.append(post)
                tcontents.append(process_content(post.content))
                tnum_comment = len(Comment.query.filter_by(post_id=post.id).all())
                tnum_comments.append(tnum_comment)

            tagposts.extend(tposts)
            tagcontents.extend(tcontents)

            tagnum_comments.extend(tnum_comments)
    return render_template('search.html', title='Search', form=form, result=searches, tagposts=tagposts, tagcontents=tagcontents, tagnum_comments=tagnum_comments, posts=explore_posts, contents=contents, num_comments=num_comments)
