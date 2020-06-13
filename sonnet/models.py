from datetime import datetime
from flask_login import UserMixin
from sonnet import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

post_likes = db.Table('post_likes',
    db.Column('user_id',db.Integer,db.ForeignKey('user.id')),
    db.Column('post_id',db.Integer,db.ForeignKey('post.id')))

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    liked = db.relationship('Post', secondary=post_likes,
                                    backref = db.backref('likers', lazy='dynamic'), lazy='dynamic')

    followed = db.relationship('User', 
                               secondary=followers, 
                               primaryjoin=(followers.c.follower_id == id), 
                               secondaryjoin=(followers.c.followed_id == id), 
                               backref=db.backref('followers', lazy='dynamic'), 
                               lazy='dynamic')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    
    def like(self, post):
        if not self.is_liking(post):
            self.liked.append(post)

    def unlike(self, post):
        if self.is_liking(post):
            self.liked.remove(post)

    def is_liking(self, post):
        return db.session.execute("SELECT COUNT(*) FROM post_likes WHERE user_id = :user_id AND post_id = :post_id", {'user_id': self.id, 'post_id': post.id}).fetchone()[0] > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    def is_followingbyid(self,user_id):
        return self.followed.filter(followers.c.followed_id == user_id).count() > 0

post_tags = db.Table('post_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    track = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.relationship('Tag', secondary=post_tags, backref=db.backref('posts', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return f"Post('{self.title}', '{self.track}',  '{self.date_posted}')"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"Tag('{self.name}')"
