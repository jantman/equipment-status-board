"""Admin forms for user management."""

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class UserCreateForm(FlaskForm):
    """Form for creating a new user account."""

    username = StringField('Username *', validators=[DataRequired(), Length(max=80)])
    email = StringField('Email *', validators=[DataRequired(), Email(), Length(max=255)])
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


class AppConfigForm(FlaskForm):
    """Form for application configuration settings."""

    tech_doc_edit_enabled = BooleanField('Allow Technicians to edit equipment documentation')
    submit = SubmitField('Save Configuration')


class ResetPasswordForm(FlaskForm):
    """Minimal form for resetting a user's password (CSRF only)."""
