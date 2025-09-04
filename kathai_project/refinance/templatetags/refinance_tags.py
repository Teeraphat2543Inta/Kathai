# refinance/templatetags/refinance_tags.py

from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        if value is None or arg is None:
            return 0
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, Exception):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        if value is None or arg is None:
            return 0
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, Exception):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        if value is None or arg is None or arg == 0:
            return 0
        return Decimal(str(value)) / Decimal(str(arg))
    except (ValueError, TypeError, Exception):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    try:
        if value is None or total is None or total == 0:
            return 0
        return (Decimal(str(value)) / Decimal(str(total))) * 100
    except (ValueError, TypeError, Exception):
        return 0

@register.filter
def currency(value):
    """Format value as currency with commas"""
    try:
        if value is None:
            return "0"
        return "{:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return "0"

@register.filter
def default_if_none(value, default):
    """Return default if value is None"""
    return default if value is None else value

@register.filter
def get_attr(obj, attr_name):
    """Return the attribute of an object dynamically"""
    return getattr(obj, attr_name, '')