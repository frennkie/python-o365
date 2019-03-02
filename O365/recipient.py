import logging


log = logging.getLogger(__name__)


class Recipient:
    """ A single Recipient """

    def __init__(self, address=None, name=None, parent=None, field=None):
        """ Create a recipient with provided information

        :param str address: email address of the recipient
        :param str name: name of the recipient
        :param HandleRecipientsMixin parent: parent recipients handler
        :param str field: name of the field to update back
        """
        self._address = address or ''
        self._name = name or ''
        self._parent = parent
        self._field = field

    def __bool__(self):
        return bool(self.address)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.name:
            return '{} ({})'.format(self.name, self.address)
        else:
            return self.address

    # noinspection PyProtectedMember
    def _track_changes(self):
        """ Update the track_changes on the parent to reflect a
        needed update on this field """
        if self._field and getattr(self._parent, '_track_changes',
                                   None) is not None:
            self._parent._track_changes.add(self._field)

    @property
    def address(self):
        """ Email address of the recipient

        :getter: Get the email address
        :setter: Set and update the email address
        :type: str
        """
        return self._address

    @address.setter
    def address(self, value):
        self._address = value
        self._track_changes()

    @property
    def name(self):
        """ Name of the recipient

        :getter: Get the name
        :setter: Set and update the name
        :type: str
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self._track_changes()


class Recipients:
    """ A Sequence of Recipients """

    def __init__(self, recipients=None, parent=None, field=None):
        """ Recipients must be a list of either address strings or
        tuples (name, address) or dictionary elements

        :param recipients: list of either address strings or
         tuples (name, address) or dictionary elements
        :type recipients: list[str] or list[tuple] or list[dict]
         or list[Recipient]
        :param HandleRecipientsMixin parent: parent recipients handler
        :param str field: name of the field to update back
        """
        self._parent = parent
        self._field = field
        self._recipients = []
        self.untrack = True
        if recipients:
            self.add(recipients)
        self.untrack = False

    def __iter__(self):
        return iter(self._recipients)

    def __getitem__(self, key):
        return self._recipients[key]

    def __contains__(self, item):
        return item in {recipient.address for recipient in self._recipients}

    def __bool__(self):
        return bool(len(self._recipients))

    def __len__(self):
        return len(self._recipients)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Recipients count: {}'.format(len(self._recipients))

    # noinspection PyProtectedMember
    def _track_changes(self):
        """ Update the track_changes on the parent to reflect a
        needed update on this field """
        if self._field and getattr(self._parent, '_track_changes',
                                   None) is not None and self.untrack is False:
            self._parent._track_changes.add(self._field)

    def clear(self):
        """ Clear the list of recipients """
        self._recipients = []
        self._track_changes()

    def add(self, recipients):
        """ Add the supplied recipients to the exiting list

        :param recipients: list of either address strings or
         tuples (name, address) or dictionary elements
        :type recipients: list[str] or list[tuple] or list[dict]
        """

        if recipients:
            if isinstance(recipients, str):
                self._recipients.append(
                    Recipient(address=recipients, parent=self._parent,
                              field=self._field))
            elif isinstance(recipients, Recipient):
                self._recipients.append(recipients)
            elif isinstance(recipients, tuple):
                name, address = recipients
                if address:
                    self._recipients.append(
                        Recipient(address=address, name=name,
                                  parent=self._parent, field=self._field))
            elif isinstance(recipients, list):
                for recipient in recipients:
                    self.add(recipient)
            else:
                raise ValueError('Recipients must be an address string, a '
                                 'Recipient instance, a (name, address) '
                                 'tuple or a list')
            self._track_changes()

    def remove(self, address):
        """ Remove an address or multiple addresses

        :param address: list of addresses to remove
        :type address: str or list[str]
        """
        recipients = []
        if isinstance(address, str):
            address = {address}  # set
        elif isinstance(address, (list, tuple)):
            address = set(address)

        for recipient in self._recipients:
            if recipient.address not in address:
                recipients.append(recipient)
        if len(recipients) != len(self._recipients):
            self._track_changes()
        self._recipients = recipients

    def get_first_recipient_with_address(self):
        """ Returns the first recipient found with a non blank address

        :return: First Recipient
        :rtype: Recipient
        """
        recipients_with_address = [recipient for recipient in self._recipients
                                   if recipient.address]
        if recipients_with_address:
            return recipients_with_address[0]
        else:
            return None


class HandleRecipientsMixin:

    def _recipients_from_cloud(self, recipients, field=None):
        """ Transform a recipient from cloud data to object data """
        recipients_data = []
        for recipient in recipients:
            recipients_data.append(
                self._recipient_from_cloud(recipient, field=field))
        return Recipients(recipients_data, parent=self, field=field)

    def _recipient_from_cloud(self, recipient, field=None):
        """ Transform a recipient from cloud data to object data """

        if recipient:
            recipient = recipient.get(self._cc('emailAddress'),
                                      recipient if isinstance(recipient,
                                                              dict) else {})
            address = recipient.get(self._cc('address'), '')
            name = recipient.get(self._cc('name'), '')
            return Recipient(address=address, name=name, parent=self,
                             field=field)
        else:
            return Recipient()

    def _recipient_to_cloud(self, recipient):
        """ Transforms a Recipient object to a cloud dict """
        data = None
        if recipient:
            data = {self._cc('emailAddress'): {
                self._cc('address'): recipient.address}}
            if recipient.name:
                data[self._cc('emailAddress')][
                    self._cc('name')] = recipient.name
        return data
