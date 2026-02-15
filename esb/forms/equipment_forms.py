"""Equipment forms for area and equipment management."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, DataRequired, Length, Optional

from esb.models.document import DOCUMENT_CATEGORIES

FORM_DOCUMENT_CATEGORIES = [('', '-- Select Category --')] + DOCUMENT_CATEGORIES


class AreaCreateForm(FlaskForm):
    """Form for creating a new area."""

    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slack_channel = StringField('Slack Channel', validators=[DataRequired(), Length(max=80)])
    submit = SubmitField('Create Area')


class AreaEditForm(FlaskForm):
    """Form for editing an existing area."""

    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slack_channel = StringField('Slack Channel', validators=[DataRequired(), Length(max=80)])
    submit = SubmitField('Save Changes')


class EquipmentCreateForm(FlaskForm):
    """Form for creating a new equipment record."""

    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(max=200)])
    model = StringField('Model', validators=[DataRequired(), Length(max=200)])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Length(max=200)])
    acquisition_date = DateField('Acquisition Date', validators=[Optional()])
    acquisition_source = StringField('Acquisition Source', validators=[Length(max=200)])
    acquisition_cost = DecimalField('Acquisition Cost', places=2, validators=[Optional()])
    warranty_expiration = DateField('Warranty Expiration', validators=[Optional()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Equipment')


class EquipmentEditForm(FlaskForm):
    """Form for editing an existing equipment record."""

    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(max=200)])
    model = StringField('Model', validators=[DataRequired(), Length(max=200)])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Length(max=200)])
    acquisition_date = DateField('Acquisition Date', validators=[Optional()])
    acquisition_source = StringField('Acquisition Source', validators=[Length(max=200)])
    acquisition_cost = DecimalField('Acquisition Cost', places=2, validators=[Optional()])
    warranty_expiration = DateField('Warranty Expiration', validators=[Optional()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Changes')


class DocumentUploadForm(FlaskForm):
    """Form for uploading a document to an equipment record."""

    file = FileField('Document', validators=[
        FileRequired('Please select a file to upload.'),
        FileAllowed(
            ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'csv', 'ppt', 'pptx'],
            'Only document files are allowed.',
        ),
    ])
    category = SelectField('Category', choices=FORM_DOCUMENT_CATEGORIES, validators=[DataRequired()])
    submit = SubmitField('Upload Document')


class PhotoUploadForm(FlaskForm):
    """Form for uploading a photo/video to an equipment record."""

    file = FileField('Photo/Video', validators=[
        FileRequired('Please select a file to upload.'),
        FileAllowed(
            ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'],
            'Only image and video files are allowed.',
        ),
    ])
    submit = SubmitField('Upload Photo')


class ExternalLinkForm(FlaskForm):
    """Form for adding an external link to an equipment record."""

    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    url = StringField('URL', validators=[DataRequired(), Length(max=2000), URL()])
    submit = SubmitField('Add Link')
