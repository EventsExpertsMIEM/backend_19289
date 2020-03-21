from flask import Blueprint
from flask_login import login_required, current_user

from . import *
from ..util import get_post_class, routes
from exproj.logic import posts as posts_logic
from exproj.validation import validate_tags, schemas

bp = Blueprint('posts', __name__)


@routes(bp, ['question', 'article'], '/all')
def get_posts():
    PostClass = get_post_class(request.path)
    args = request.args

    offset = args.get('offset')
    limit = args.get('limit')
    closed = args.get('closed')
    tag_ids = (list(map(int, args['tags'].split(','))) if 'tags' in args
               else None)

    posts = posts_logic.get_many(PostClass, None, closed,
                                 tag_ids, offset, limit)

    return jsonify(posts)


@routes(bp, ['question', 'article'], methods=['POST'])
@login_required
def create_post():
    PostClass = get_post_class(request.path)
    data = get_json()

    schemas.question.validate(data)
    if data['closed'] is True and not current_user.has_access('expert'):
        abort(422, 'You cannot create closed questions')
    validate_tags(data['tags'])

    p_id = posts_logic.create(PostClass, data)
    return make_ok(f'{PostClass.__name__} #{p_id} successfully created'), 201


@routes(bp, ['question', 'article'], '/<int:p_id>')
def get_post(p_id):
    PostClass = get_post_class(request.path)
    post = posts_logic.get(PostClass, p_id)
    return jsonify(post)


@routes(bp, ['question', 'article'], '/<int:p_id>', methods=['DELETE'])
@login_required
def delete_post(p_id):
    PostClass = get_post_class(request.path)
    posts_logic.delete(PostClass, p_id)
    return make_ok(f'{PostClass.__name__} #{p_id} has been deleted')


@routes(bp, ['question', 'article'], '/<int:p_id>', methods=['PUT'])
@login_required
def update_post(p_id):
    PostClass = get_post_class(request.path)
    data = get_json()
    # schemas.post_update.validate(data)
    if 'tags' in data.keys():
        validate_tags(data['tags'])
    posts_logic.update(PostClass, p_id, data)
    return make_ok(f'{PostClass.__name__} #{p_id} has been updated')


# todo
@routes(bp, ['question', 'article'], '/<int:p_id>/increase_views')
def increase_post_views(p_id):
    PostClass = get_post_class(request.path)
    posts_logic.increase_views(PostClass, p_id)
    return make_ok('Successfully increased '
                   f'{PostClass.__name__.lower()}\'s #{p_id} views')


@routes(bp, ['question', 'article', 'comment'], '/<int:p_id>/toggle_upvote')
@routes(bp, ['question', 'article', 'comment'], '/<int:p_id>/toggle_downvote')
@login_required
def vote_post(p_id):
    PostClass = get_post_class(request.path)
    action = ('up'
              if request.path[request.path.rfind('/') + 1:] == 'toggle_upvote'
              else 'down')
    result = posts_logic.toggle_vote(PostClass, p_id, action)
    if result == 'deleted':
        message = 'Successfully deleted vote '\
                  f'for {PostClass.__name__.lower()} #{p_id}'
    else:
        message = f'Successfully {action}voted '\
                  f'{PostClass.__name__.lower()} #{p_id}'
    return jsonify(message)


@routes(bp, ['question', 'article'], '/<int:p_id>/comments')
def get_post_comments(p_id):
    PostClass = get_post_class(request.path)
    comments = posts_logic.get_post_comments(PostClass, p_id)
    return jsonify(comments)


@routes(bp, ['question', 'article'], '/<int:p_id>/comment', methods=['POST'])
@login_required
def create_comment(p_id):
    PostClass = get_post_class(request.path)
    data = get_json()
    text = data['text']
    posts_logic.create_comment(PostClass, p_id, text)
    return make_ok(f'Comment for the {PostClass.__name__.lower()} '
                   f'#{p_id} has been created'), 201