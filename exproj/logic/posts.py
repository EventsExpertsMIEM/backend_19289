from flask import abort
from flask_login import current_user

from . import slice
from exproj import logger
from exproj.db import (get_session, Question, Article, Tag, Comment, User,
                       DCommentVotes, DPostVotes)


def get_many(PostClass, u_id=None, closed=None,
             tags=None, offset=None, limit=None, archived=None):
    with get_session() as s:
        query = (
            s.query(PostClass)
            .filter(PostClass.status == ('archived' if archived else 'active'))
            .order_by(PostClass.creation_date.desc())
        )

        if u_id:
            if not s.query(User).filter_by(id=u_id).count():
                abort(404, f'User with id #{u_id} not found')

            query = query.filter(PostClass.u_id == u_id)

        if tags:
            query = query.filter(PostClass.tags.any(Tag.name.in_(tags)))

        if PostClass == Question:
            if closed and closed != '0':
                if PostClass != Question:
                    abort(422, '`closed` parameter is'
                               ' available only for questions')

                if (not current_user.has_access('expert')
                        and current_user.id != u_id):
                    abort(403, 'You can\'t view closed questions')

                query = query.filter(Question.closed.is_(True))
            else:
                query = query.filter(Question.closed.is_(False))

        data = slice(query, offset, limit)

        posts = [p.as_dict() for p in data]
        return posts


def get(PostClass, p_id):
    with get_session() as s:
        p = s.query(PostClass).get(p_id)
        if (not p or p.status == 'deleted'
                or (p.status == 'archived' and current_user.id != p.u_id
                    and not current_user.has_access('moderator'))):
            abort(404)

        if (PostClass == Question and p.closed
                and not current_user.has_access('expert')
                and p.u_id != current_user.id):
            abort(403)

        return p.as_dict()


def create(PostClass, data):
    u_id = current_user.id

    with get_session() as s:
        s.add(current_user)

        if PostClass == Question:
            p = Question(u_id=u_id, title=data['title'], body=data['body'],
                         only_experts_answer=data['only_experts_answer'],
                         only_chosen_tags=data['only_chosen_tags'],
                         closed=data['closed'])
        elif PostClass == Article:
            p = Article(u_id=u_id, title=data['title'], body=data['body'])

        # assigning tags to a post from data
        p.tags = s.query(Tag).filter(Tag.name.in_(data['tags'])).all()

        s.add(p)
        s.commit()

        if PostClass == Question:
            current_user.question_count += 1
        elif PostClass == Article:
            current_user.article_count += 1

        return p.id  # return created question's id


def delete(PostClass, p_id):
    with get_session() as s:
        s.add(current_user)

        p = PostClass.get_or_404(s, p_id)

        if (not current_user.has_access('moderator')
                and p.u_id != current_user.id):
            abort(403)

        if PostClass == Question:
            current_user.question_count -= 1
        elif PostClass == Article:
            current_user.article_count -= 1

        for comment in p.comments.all():
            comment.author.comment_count -= 1
            comment.status = 'deleted'

        p.status = 'deleted'


def _archive(PostClass, p_id, cancel):
    with get_session() as s:
        if PostClass == Comment:
            raise TypeError('Cannot archive comment')

        p = s.query(PostClass).get(p_id)
        if not p or p.status == 'deleted':
            abort(404, f'{PostClass.__name__} with id #{p_id} not found')

        if (not current_user.has_access('moderator')
                and p.u_id != current_user.id):
            abort(403)

        p.status = 'archived' if not cancel else 'active'


def archive(PostClass, p_id):
    _archive(PostClass, p_id, False)


def unarchive(PostClass, p_id):
    _archive(PostClass, p_id, True)


def update(PostClass, p_id, new_data):
    with get_session() as s:
        p = PostClass.get_or_404(s, p_id)

        if (not current_user.has_access('moderator')
                and p.u_id != current_user.id):
            abort(403)

        for param, value in new_data.items():
            if param == 'tags':
                p.tags = s.query(Tag).filter(Tag.name.in_(value)).all()
            else:
                setattr(p, param, value)

        return p.as_dict()


# todo
def increase_views(PostClass, p_id):
    with get_session() as s:
        p = PostClass.get_or_404(s, p_id)
        p.view_count += 1


def toggle_vote(PostClass, p_id, action):
    u_id = current_user.id

    with get_session() as s:
        p = PostClass.get_or_404(s, p_id)
        if (PostClass == Question and p.closed
                and not current_user.has_access('expert')):
            abort(403)

        if PostClass == Comment:
            if (isinstance(p.post, Question) and p.post.closed
                    and not current_user.has_access('expert')):
                abort(403)
            cur_vote = s.query(DCommentVotes).get((u_id, p_id))
            new_vote = DCommentVotes(u_id=u_id, c_id=p_id)
        else:
            cur_vote = s.query(DPostVotes).get((u_id, p_id))
            new_vote = DPostVotes(u_id=u_id, p_id=p_id)

        if action == 'up':
            if cur_vote:
                if cur_vote.upvoted:
                    s.delete(cur_vote)
                    p.score -= 1
                    p.author.rating -= 1
                    return 'deleted'
                else:
                    p.score += 2
                    p.author.rating += 2
                    cur_vote.upvoted = True
            else:
                p.score += 1
                p.author.rating += 1
                new_vote.upvoted = True
                s.add(new_vote)
            return 'up'
        elif action == 'down':
            if cur_vote:
                if not cur_vote.upvoted:
                    s.delete(cur_vote)
                    p.score += 1
                    p.author.rating += 1
                    return 'deleted'
                else:
                    p.score -= 2
                    p.author.rating -= 2
                    cur_vote.upvoted = False
            else:
                p.score -= 1
                p.author.rating -= 1
                new_vote.upvoted = False
                s.add(new_vote)
            return 'down'
        else:
            raise ValueError('Action should be only `up` or `down`')


def get_post_comments(PostClass, p_id, offset=None, limit=None):
    with get_session() as s:
        p = PostClass.get_or_404(s, p_id)

        if (PostClass == Question and p.closed
                and not current_user.has_access('expert')):
            abort(403, 'You must be an expert')

        query = (p.comments
                 .filter(Comment.status == 'active')
                 .order_by(Comment.creation_date.desc()))

        data = slice(query, offset, limit)
        comments = [c.as_dict() for c in data]
        return comments


def create_comment(PostClass, p_id, text):
    u_id = current_user.id

    with get_session() as s:
        s.add(current_user)
        p = PostClass.get_or_404(s, p_id)

        if PostClass == Question and not current_user.can_answer(p):
            abort(403, 'You cant create answer because you are not an expert or'
                       ' do not have expert status in the areas of question')

        comment = Comment(u_id=u_id, p_id=p_id, text=text)
        p.comments.append(comment)
        p.comment_count += 1
        current_user.comment_count += 1
