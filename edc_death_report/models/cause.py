from edc_base.model.models import BaseListModel


class Cause (BaseListModel):

    class Meta:
        ordering = ['display_index']
        app_label = 'edc_death_report'