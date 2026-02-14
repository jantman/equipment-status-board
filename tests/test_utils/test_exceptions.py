"""Tests for domain exception hierarchy."""

from esb.utils.exceptions import (
    ESBError,
    EquipmentNotFound,
    RepairRecordNotFound,
    UnauthorizedAction,
    ValidationError,
)


class TestESBError:
    """Tests for ESBError base class."""

    def test_is_exception(self):
        """ESBError inherits from Exception."""
        assert issubclass(ESBError, Exception)

    def test_can_raise_and_catch(self):
        """ESBError can be raised and caught."""
        with __import__('pytest').raises(ESBError):
            raise ESBError('test error')

    def test_message(self):
        """ESBError preserves the error message."""
        err = ESBError('something went wrong')
        assert str(err) == 'something went wrong'


class TestEquipmentNotFound:
    """Tests for EquipmentNotFound exception."""

    def test_inherits_from_esb_error(self):
        assert issubclass(EquipmentNotFound, ESBError)

    def test_caught_by_esb_error(self):
        with __import__('pytest').raises(ESBError):
            raise EquipmentNotFound('equipment 42 not found')


class TestRepairRecordNotFound:
    """Tests for RepairRecordNotFound exception."""

    def test_inherits_from_esb_error(self):
        assert issubclass(RepairRecordNotFound, ESBError)

    def test_caught_by_esb_error(self):
        with __import__('pytest').raises(ESBError):
            raise RepairRecordNotFound('repair record 7 not found')


class TestUnauthorizedAction:
    """Tests for UnauthorizedAction exception."""

    def test_inherits_from_esb_error(self):
        assert issubclass(UnauthorizedAction, ESBError)

    def test_caught_by_esb_error(self):
        with __import__('pytest').raises(ESBError):
            raise UnauthorizedAction('not allowed')


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_inherits_from_esb_error(self):
        assert issubclass(ValidationError, ESBError)

    def test_caught_by_esb_error(self):
        with __import__('pytest').raises(ESBError):
            raise ValidationError('invalid input')
