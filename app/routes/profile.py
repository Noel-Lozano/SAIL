from flask import Flask, render_template, redirect, url_for, session, flash, request, Blueprint
from app.models.models import db, User, Place, Search

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'], endpoint='profile')
def profile():
    if 'user_id' not in session:
        flash("You must be logged in to view your profile.", "danger")
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Update user profile information
        user.username = request.form.get('username')
        user.interests = request.form.get('interests')
        user.ai_enabled = (request.form.get('ai_enabled') == 'true')
        db.session.commit()

        session['user'] = user.username # update username
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile.profile'))
    

    user_profile = {
        "interests": user.interests or "No interests specified",
        "ai_enabled": user.ai_enabled
    }

    return render_template('profile.html', user=user, user_profile=user_profile)