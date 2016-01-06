﻿"""
Author: Swagger.pro
File: models.py
Purpose: database definitions for SQLAlchemy
"""
from swagmail import db
from .errors import ValidationError
from re import search, match
from os import urandom
from passlib.hash import sha512_crypt as sha512  # pylint: disable=no-name-in-module
from hashlib import sha1


class VirtualDomains(db.Model):
    """ A table to house the email domains
    """
    __table_name__ = 'virtual_domains'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True,
                   nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<virtual_domains(name=\'%s\')>' % (self.name)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def from_json(self, json):
        if json.get('name', None) in [None, ""]:
            raise ValidationError('The domain name was not specified')
        if self.query.filter_by(name=json['name']).first() is None:
            self.name = json['name']
        else:
            raise ValidationError('The domain "%s" already exists' % json['name'])
        return self


    def query_from_json(self, json):
        if json.get('name', None) is None:
            raise ValidationError('Invalid domain: missing ' + e.args[0])
        if self.query.filter_by(name=json['name']).first() is not None:
            return self.query.filter_by(name=json['name']).first()
        else:
            raise ValidationError('The domain "%s" does not exist' % json['name'])
        return self


class VirtualUsers(db.Model):
    """ A table to house the email user accounts
    """
    __table_name__ = 'virtual_users'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey(
        'virtual_domains.id', ondelete='CASCADE'), nullable=False)
    password = db.Column(db.String(106), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<virtual_users(email=\'%s\')>' % (self.email)

    def to_json(self):
        """ Leaving password out
        """
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'email': self.email
        }

    def from_json(self, json):
        if json.get('email', None) is None:
            raise ValidationError('The email address was not specified')
        if json.get('password', None) is None:
            raise ValidationError('The password was not specified')
        if self.query.filter_by(email=json['email']).first() is not None:
            raise ValidationError('"%s" already exists!' % json['email'])
        self.email = json['email']
        # Checks if the domain can be extracted and if the email is at least
        # somewhat in the right format
        if search('(?<=@).*$', json['email']) and match('.*@.*[.].*$', json['email']):
            domain = search('(?<=@).*$', json['email']).group(0)
            if VirtualDomains.query.filter_by(name=domain).first() is not None:
                self.domain_id = VirtualDomains.query.filter_by(
                    name=domain).first().id
                self.password = self.encrypt_password(json['password'])
            else:
                raise ValidationError(
                    'The domain "%s" is not managed by this database' % domain)
        else:
            raise ValidationError(
                '"%s" is not a valid email address' % json['email'])
        return self

    def encrypt_password(self, password):
        salt = (sha1(urandom(16)).hexdigest())[:16]
        protectedPassword = sha512.encrypt(password, rounds=5000,
                                    salt=salt, implicit_rounds=True)
        return protectedPassword


class VirtualAliases(db.Model):
    """ A table to house the email aliases
    """
    __table_name__ = 'virtual_aliases'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey(
        'virtual_domains.id', ondelete='CASCADE'), nullable=False)
    source = db.Column(db.String(100), unique=True, nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<virtual_aliases(source=\'%s\')>' % (self.source)

    def to_json(self):
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'source': self.source,
            'destination': self.destination
        }

    def from_json(self, json):
        if json.get('source', None) is None:
            raise ValidationError('The source email was not specified')
        if json.get('destination', None) is None:
            raise ValidationError('The destination email was not specified')
        if self.query.filter_by(source=json['source'], destination=json['destination']).first() is not None:
            raise ValidationError('"%s" to "%s" already exists!' % (
                json['source'], json['destination']))
        if self.validate_source(json['source']):
            self.source = json['source']
        if self.validate_destination(json['destination']):
            self.destination = json['destination']
            self.domain_id = VirtualDomains.query.filter_by(name=search(
                    '(?<=@).*$', json['destination']).group(0)).first().id
        return self

    def validate_source(self, source):
        if match('.*@.*[.].*$', source):
            sourceDomain = search('(?<=@).*$', source).group(0)
            if VirtualAliases.query.filter_by(source=source).first() is not None:
                raise ValidationError(
                    'The source alias "%s" already exists' % source)
            if VirtualUsers.query.filter_by(email=source).first() is not None:
                raise ValidationError(
                    'The source alias "%s" is an existing email address' % source)
            if VirtualDomains.query.filter_by(name=sourceDomain).first() is None:
                raise ValidationError(
                    'The domain "%s" is not managed by this database' % sourceDomain)
            return True
        else:
            raise ValidationError(
                'The source "%s" is not in a valid email format' % source)

    def validate_destination(self, destination):
        if match('.*@.*[.].*$', destination):
            destinationDomain = search(
                '(?<=@).*$', destination).group(0)
            if VirtualDomains.query.filter_by(name=destinationDomain).first() is None:
                raise ValidationError(
                    'The domain "%s" is not managed by this database' % destinationDomain)
            if VirtualUsers.query.filter_by(email=destination).first() is not None:
                return True
            else:
                raise ValidationError \
                    ('The destination "%s" is not a current email address' % destination)
        else:
            raise ValidationError(
                'The destination "%s" is not in a valid email format' % destination)


class Admins(db.Model):
    """ A table to house the admin users
    """
    __tablename__ = 'swagmail_admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)

    def __init__(self, name, email, password, authenticated, active):
        self.name = name
        self.email = email
        self.password = password
        self.active = active

    def is_active(self):
        """ Returns if user is active
        """
        return self.active

    def get_id(self):
        """ Returns id of user
        """
        return self.id

    def is_authenticated(self):
        """ Returns if user is authenticated
        This is hooked by flask-login.
        query using current_user.is_authenticated()
        """
        return True

    def is_anonymous(self):
        """ Returns if guest
        """
        # Anonymous users are not supported
        return False

    def __repr__(self):
        return '<swagmail_admins(email=\'%s\')>' % (self.email)