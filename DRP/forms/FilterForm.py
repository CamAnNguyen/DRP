"""Abstract classes for creating search forms."""
from django import forms
from operator import or_, and_


class FilterForm(forms.Form):

    """An abstract form class (though not formally an ABC) for performing filter-like searching on data."""

    def is_empty(self):
        """Method fails for foreignkey and many to many fields, for whuich you will need to implement your own methods."""
        if hasattr(self, 'checkFields'):
            keys = self.checkFields
        else:
            keys = self.fields.keys()

        return all(self.cleaned_data.get(key) in self.fields[key].empty_values for key in keys)

    def fetch(self):
        """Should be overridden to return a queryset."""
        pass


class FilterFormSet(forms.formsets.BaseFormSet):

    """A formset specifically for use with FilterForms."""

    model = None

    def __init__(self, operator=or_, *args, **kwargs):
        """
        Implement a lot of arguments which BaseFormSets expect to be issued by the formsetfactories.

        the operator should be or_ or and_ importoed from the operator module, and defines the behaviour
        of merging the querysets resulting from each FilterForm; or_ will cause the result of the
        fetch() method to be the union of all results, whilst and_ will cause the result to be
        the intersection thereof.
        """
        self.extra = 1
        self.can_delete = False
        self.can_order = False
        self.validate_min = False  # this is required for django 1.7
        # this is required for django 1.7. Unclear to me why both are required,
        # but they are.
        self.min_num = 0
        self.max_num = 10000
        self.validate_max = False
        self.absolute_max = 10000
        if operator in (or_, and_):
            self._operator = operator
        else:
            raise TypeError(
                'Invalid logical query operator selected, please use operator.or_ or operator.and_')
        super(FilterFormSet, self).__init__(*args, **kwargs)

    @property
    def cleaned_data(self):
        """Return a list of cleaned data from each valid, non-empty form, each entry is a dictionary."""
        initData = []
        for form in self:
            if form.is_valid() and not form.is_empty():
                initData.append(form.cleaned_data)
        return initData

    def is_empty(self):
        """Indicate whether the entire formset is empty."""
        return all(form.is_empty() for form in self)

    def fetch(self):
        """Fetche a queryset which merges the results from each filter form."""
        if self.model is not None:
            if self._operator == or_:
                qs = self.model.objects.none()
            elif self._operator == and_:
                qs = self.model.objects.all()
            else:
                raise TypeError('Invalid logical query operator provided')
        else:
            qs = self.forms[0].fetch()
        for form in self:
            if not form.is_empty():
                qs = self._operator(qs, form.fetch())
        return qs


def filterFormSetFactory(formClass, modelClass):
    """A factory for use with filterFormSets."""
    class FilterFormSetDerivative(FilterFormSet):

        """A very thin descendent for a FilterFormSet which is generated by the filterFormsetFactory."""

        form = formClass
        model = modelClass

    return FilterFormSetDerivative
