"""Tests for esb.utils.text helpers."""

import pytest

from esb.utils.text import get_normalized_base_url, slugify_filename


class TestSlugifyFilename:
    def test_normal_alnum(self):
        assert slugify_filename('TableSaw1') == 'TableSaw1'

    def test_spaces_to_hyphens(self):
        assert slugify_filename('Table Saw 1') == 'Table-Saw-1'

    def test_accented_transliterates(self):
        assert slugify_filename('Café') == 'Cafe'

    def test_multi_run_punctuation_collapsed(self):
        assert slugify_filename('Table!!!Saw///1') == 'Table-Saw-1'

    def test_empty_string_fallback(self):
        assert slugify_filename('') == 'equipment'

    def test_none_fallback(self):
        assert slugify_filename(None) == 'equipment'

    def test_long_truncated_to_50(self):
        result = slugify_filename('A' * 100)
        assert len(result) == 50
        assert result == 'A' * 50

    def test_leading_trailing_punctuation_stripped(self):
        assert slugify_filename('---TableSaw---') == 'TableSaw'

    def test_only_punctuation_fallback(self):
        assert slugify_filename('!!!') == 'equipment'

    def test_cjk_only_fallback(self):
        assert slugify_filename('機械') == 'equipment'

    def test_truncation_lands_on_hyphen_no_trailing_dash(self):
        # 49 A's + '-abc' → after substitution, 49 A's + '-abc' (53 chars).
        # [:50] = 49 A's + '-'. Without a final .strip('-'), this produced a
        # trailing hyphen in the filename.
        name = 'A' * 49 + '-abc'
        result = slugify_filename(name)
        assert not result.endswith('-'), f'trailing hyphen in {result!r}'
        assert result == 'A' * 49


class TestGetNormalizedBaseUrl:
    # -- Happy path --

    def test_bare_host(self):
        assert get_normalized_base_url('http://host') == 'http://host'

    def test_host_port_trailing_slash_stripped(self):
        assert get_normalized_base_url('https://host:8080/') == 'https://host:8080'

    def test_multiple_trailing_slashes_stripped(self):
        assert get_normalized_base_url('http://host///') == 'http://host'

    def test_whitespace_padded_trimmed(self):
        assert get_normalized_base_url('  http://host  ') == 'http://host'

    def test_scheme_lowercased_host_preserved(self):
        assert get_normalized_base_url('HTTP://Host:8080') == 'http://Host:8080'

    # -- Empty --

    def test_empty_raises(self):
        with pytest.raises(ValueError, match='not configured'):
            get_normalized_base_url('')

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match='not configured'):
            get_normalized_base_url('   ')

    def test_none_raises(self):
        with pytest.raises(ValueError, match='not configured'):
            get_normalized_base_url(None)

    # -- Embedded whitespace / non-ASCII --

    def test_zero_width_space_raises(self):
        with pytest.raises(ValueError, match='ASCII|whitespace'):
            get_normalized_base_url('http://host\u200bcom')

    def test_embedded_tab_raises(self):
        with pytest.raises(ValueError, match='ASCII|whitespace'):
            get_normalized_base_url('http://host\tcom')

    def test_embedded_space_raises(self):
        with pytest.raises(ValueError, match='ASCII|whitespace'):
            get_normalized_base_url('http:// host.com')

    # -- Bad scheme --

    @pytest.mark.parametrize('url', [
        'javascript:alert(1)',
        'ftp://host',
        'data:text/plain,x',
        'file:///tmp/x',
    ])
    def test_bad_scheme_raises(self, url):
        with pytest.raises(ValueError, match=r'http\(s\) URL'):
            get_normalized_base_url(url)

    def test_no_scheme_raises(self):
        with pytest.raises(ValueError, match=r'http\(s\) URL'):
            get_normalized_base_url('host.example.com')

    # -- Missing host --

    def test_http_no_host_raises(self):
        with pytest.raises(ValueError, match='host'):
            get_normalized_base_url('http://')

    def test_https_no_host_with_path_raises(self):
        # 'https:///path' has no trailing slash to rstrip; urlsplit parses as
        # scheme='https', netloc='', path='/path'. Empty netloc → missing host.
        with pytest.raises(ValueError, match='host'):
            get_normalized_base_url('https:///path')

    # -- Credentials --

    def test_credentials_raises(self):
        with pytest.raises(ValueError, match='credentials'):
            get_normalized_base_url('http://user:pass@host')

    # -- Path/query/fragment --

    def test_path_raises(self):
        with pytest.raises(ValueError, match='path, query, or fragment'):
            get_normalized_base_url('http://host/api')

    def test_query_raises(self):
        with pytest.raises(ValueError, match='path, query, or fragment'):
            get_normalized_base_url('http://host?a=1')

    def test_fragment_raises(self):
        with pytest.raises(ValueError, match='path, query, or fragment'):
            get_normalized_base_url('http://host#f')

    # -- Malformed --

    def test_malformed_ipv6_raises(self):
        with pytest.raises(ValueError, match='malformed|host|http'):
            get_normalized_base_url('https://[invalid')

    # -- Port range --

    @pytest.mark.parametrize('url', [
        'http://host:99999',
        'http://host:65536',
        'http://host:-1',
    ])
    def test_port_out_of_range_raises(self, url):
        with pytest.raises(ValueError, match='port'):
            get_normalized_base_url(url)

    def test_valid_port_accepted(self):
        assert get_normalized_base_url('http://host:65535') == 'http://host:65535'
