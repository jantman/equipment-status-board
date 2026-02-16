"""Tests for the static page service."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from esb.services import static_page_service


class TestGenerate:
    """Tests for generate()."""

    def test_returns_html_with_area_and_equipment(self, app, make_area, make_equipment):
        """generate() renders HTML with area and equipment data."""
        area = make_area(name='Woodshop')
        make_equipment(name='SawStop', area=area)

        html = static_page_service.generate()

        assert 'Woodshop' in html
        assert 'SawStop' in html

    def test_produces_self_contained_html(self, app, make_area, make_equipment):
        """generate() produces HTML with no external CSS/JS links."""
        area = make_area(name='TestArea')
        make_equipment(name='TestEquip', area=area)

        html = static_page_service.generate()

        assert '<link' not in html
        assert '<script src=' not in html
        assert '<!DOCTYPE html>' in html

    def test_includes_status_dot_classes(self, app, make_area, make_equipment):
        """generate() includes status dot CSS classes."""
        area = make_area(name='TestArea')
        make_equipment(name='TestEquip', area=area)

        html = static_page_service.generate()

        assert 'status-green' in html

    def test_includes_generated_timestamp(self, app, make_area, make_equipment):
        """generate() includes a generation timestamp."""
        area = make_area(name='TestArea')
        make_equipment(name='TestEquip', area=area)

        html = static_page_service.generate()

        assert 'Generated:' in html
        assert 'UTC' in html

    def test_includes_csp_meta_tag(self, app, make_area, make_equipment):
        """generate() includes Content-Security-Policy meta tag."""
        area = make_area(name='TestArea')
        make_equipment(name='TestEquip', area=area)

        html = static_page_service.generate()

        assert 'Content-Security-Policy' in html


class TestPushLocal:
    """Tests for push() with method='local'."""

    def test_writes_file_to_target_directory(self, app, tmp_path):
        """push() with method='local' writes index.html to target directory."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 'local'
        app.config['STATIC_PAGE_PUSH_TARGET'] = str(tmp_path)

        static_page_service.push('<html>test</html>')

        output_file = tmp_path / 'index.html'
        assert output_file.exists()
        assert output_file.read_text() == '<html>test</html>'

    def test_creates_directory_if_needed(self, app, tmp_path, capture):
        """push() with method='local' creates target directory if it doesn't exist."""
        target = str(tmp_path / 'new_subdir')
        app.config['STATIC_PAGE_PUSH_METHOD'] = 'local'
        app.config['STATIC_PAGE_PUSH_TARGET'] = target

        static_page_service.push('<html>test</html>')

        assert os.path.exists(os.path.join(target, 'index.html'))


class TestPushS3:
    """Tests for push() with method='s3'."""

    def test_calls_boto3_put_object(self, app, capture):
        """push() with method='s3' calls boto3 put_object with correct params."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 's3'
        app.config['STATIC_PAGE_PUSH_TARGET'] = 'my-bucket/status/index.html'

        import boto3
        mock_s3 = MagicMock()

        with patch.object(boto3, 'client', return_value=mock_s3) as mock_client:
            static_page_service.push('<html>test</html>')

            mock_client.assert_called_once_with('s3')
            mock_s3.put_object.assert_called_once_with(
                Bucket='my-bucket',
                Key='status/index.html',
                Body=b'<html>test</html>',
                ContentType='text/html; charset=utf-8',
                CacheControl='no-cache, no-store, must-revalidate',
            )

    def test_handles_client_error(self, app):
        """push() with method='s3' handles ClientError by raising RuntimeError."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 's3'
        app.config['STATIC_PAGE_PUSH_TARGET'] = 'my-bucket/index.html'

        import boto3
        from botocore.exceptions import ClientError

        mock_s3 = MagicMock()
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        mock_s3.put_object.side_effect = ClientError(error_response, 'PutObject')

        with patch.object(boto3, 'client', return_value=mock_s3):
            with pytest.raises(RuntimeError, match='S3 upload failed'):
                static_page_service.push('<html>test</html>')

    def test_default_key_when_no_path(self, app, capture):
        """push() with method='s3' defaults key to index.html when target has no path."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 's3'
        app.config['STATIC_PAGE_PUSH_TARGET'] = 'my-bucket'

        import boto3
        mock_s3 = MagicMock()

        with patch.object(boto3, 'client', return_value=mock_s3):
            static_page_service.push('<html>test</html>')

            call_kwargs = mock_s3.put_object.call_args[1]
            assert call_kwargs['Bucket'] == 'my-bucket'
            assert call_kwargs['Key'] == 'index.html'


class TestPushErrors:
    """Tests for push() error handling."""

    def test_empty_target_raises_runtime_error(self, app):
        """push() with empty target raises RuntimeError."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 'local'
        app.config['STATIC_PAGE_PUSH_TARGET'] = ''

        with pytest.raises(RuntimeError, match='STATIC_PAGE_PUSH_TARGET is not configured'):
            static_page_service.push('<html>test</html>')

    def test_unknown_method_raises_runtime_error(self, app):
        """push() with unknown method raises RuntimeError."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 'ftp'
        app.config['STATIC_PAGE_PUSH_TARGET'] = '/tmp/test'

        with pytest.raises(RuntimeError, match='Unknown STATIC_PAGE_PUSH_METHOD'):
            static_page_service.push('<html>test</html>')


class TestPushMutationLogging:
    """Tests for mutation logging on push."""

    def test_logs_mutation_on_local_push(self, app, tmp_path, capture):
        """push() logs a mutation event on successful local push."""
        app.config['STATIC_PAGE_PUSH_METHOD'] = 'local'
        app.config['STATIC_PAGE_PUSH_TARGET'] = str(tmp_path)

        static_page_service.push('<html>test</html>')

        assert len(capture.records) == 1
        log_data = json.loads(capture.records[0].message)
        assert log_data['event'] == 'static_page.pushed'
        assert log_data['data']['method'] == 'local'


class TestGenerateAndPush:
    """Tests for generate_and_push()."""

    def test_calls_generate_then_push(self, app):
        """generate_and_push() calls generate() then push()."""
        with patch.object(static_page_service, 'generate', return_value='<html>mock</html>') as mock_gen, \
             patch.object(static_page_service, 'push') as mock_push:
            static_page_service.generate_and_push()

            mock_gen.assert_called_once()
            mock_push.assert_called_once_with('<html>mock</html>')
