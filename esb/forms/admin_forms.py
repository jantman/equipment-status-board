"""Admin forms for user management."""

from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email


class UserCreateForm(FlaskForm):
    """Form for creating a new user account."""

    username = StringField('Username *', validators=[DataRequired()])
    email = StringField('Email *', validators=[DataRequired(), Email()])
    slack_handle = StringField('Slack Handle')
    role = SelectField(
        'Role *',
        choices=[('technician', 'Technician'), ('staff', 'Staff')],
        validators=[DataRequired()],
    )
    submit = SubmitField('Create User')


class RoleChangeForm(FlaskForm):
    """Inline form for changing a user's role on the user list."""

    user_id = HiddenField('user_id', validators=[DataRequired()])
    role = SelectField(
        'Role',
        choices=[('technician', 'Technician'), ('staff', 'Staff')],
        validators=[DataRequired()],
    )
