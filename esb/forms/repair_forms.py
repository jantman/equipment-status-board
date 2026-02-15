"""Repair record forms."""

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from esb.models.repair_record import REPAIR_SEVERITIES


class RepairRecordCreateForm(FlaskForm):
    """Form for creating a new repair record."""

    equipment_id = SelectField('Equipment *', coerce=int)
    description = TextAreaField(
        'Description *', validators=[DataRequired(), Length(max=5000)],
    )
    severity = SelectField(
        'Severity',
        choices=[('', '-- Select Severity --')] + [(s, s) for s in REPAIR_SEVERITIES],
        validators=[Optional()],
    )
    assignee_id = SelectField('Assignee', coerce=int, validators=[Optional()])
    has_safety_risk = BooleanField('Safety Risk')
    is_consumable = BooleanField('Consumable Issue')
    submit = SubmitField('Create Repair Record')


class RepairRecordUpdateForm(FlaskForm):
    """Form for updating a repair record."""

    status = SelectField('Status *', validators=[DataRequired()])
    severity = SelectField(
        'Severity',
        choices=[('', '-- No Severity --')] + [(s, s) for s in REPAIR_SEVERITIES],
        validators=[Optional()],
    )
    assignee_id = SelectField('Assignee', coerce=int, validators=[Optional()])
    eta = DateField('ETA', validators=[Optional()])
    specialist_description = TextAreaField(
        'Specialist Description',
        validators=[Optional(), Length(max=5000)],
    )
    note = TextAreaField('Add Note', validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Save Changes')
