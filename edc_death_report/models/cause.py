from edc_base.model_mixins import BaseModel, ListModelMixin


class Cause (ListModelMixin, BaseModel):

    class Meta:
        ordering = ['display_index']
        app_label = 'edc_death_report'
