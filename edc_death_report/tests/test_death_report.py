from dateutil.relativedelta import relativedelta

from django import forms
from django.db import models
from django.utils import timezone

from edc_death_report.models.death_report_mixin import DeathReportMixin
from edc_base.model.models.base_uuid_model import BaseUuidModel
from edc_death_report.models.cause import Cause
from edc_death_report.models.cause_category import CauseCategory
from edc_death_report.models.diagnosis_code import DiagnosisCode
from edc_death_report.models.medical_responsibility import MedicalResponsibility
from edc_death_report.forms.death_report_form_mixin import DeathReportFormMixin
from edc_constants.constants import YES, NO
from edc_visit_tracking.models import BaseVisitTracking, PreviousVisitMixin
from edc.entry_meta_data.models import MetaDataMixin
from edc_offstudy.models import OffStudyModelMixin, OffStudyMixin
from edc.subject.registration.models.registered_subject import RegisteredSubject
from edc_death_report.models.reason_hospitalized import ReasonHospitalized

from .base_test import BaseTest


class VisitModel(OffStudyMixin, MetaDataMixin, PreviousVisitMixin, BaseVisitTracking):

    OFF_STUDY_MODEL = ('edc_death_report', 'OffStudyModel')

    REQUIRES_PREVIOUS_VISIT = True

    def get_subject_identifier(self):
        return self.appointment.registered_subject.subject_identifier

    def custom_post_update_entry_meta_data(self):
        pass

    def get_requires_consent(self):
        return False

    class Meta:
        app_label = 'edc_death_report'


class OffStudyModel(OffStudyModelMixin, BaseUuidModel):

    VISIT_MODEL = VisitModel

    registered_subject = models.OneToOneField(RegisteredSubject)

    class Meta:
        app_label = 'edc_death_report'


class DeathReport(DeathReportMixin, BaseUuidModel):

    registered_subject = models.OneToOneField(RegisteredSubject)

    class Meta:
        app_label = 'edc_death_report'


class DeathReportForm(DeathReportFormMixin, forms.ModelForm):

    class Meta:
        model = DeathReport
        fields = '__all__'


class TestDeathReport(BaseTest):

    def setUp(self):
        super(TestDeathReport, self).setUp()
        if not self.registered_subject.registration_datetime:
            self.registered_subject.registration_datetime = timezone.now() - relativedelta(weeks=3)
            self.registered_subject.dob = self.test_consent.dob
            self.registered_subject.save()
        self.data = {
            'comment': None,
            'death_date': timezone.now().date(),
            'illness_duration': 1,
            'perform_autopsy': NO,
            'cause': Cause.objects.all().first().id,
            'cause_category': CauseCategory.objects.all().first().id,
            'cause_category_other': None,
            'cause_other': None,
            'medical_responsibility': MedicalResponsibility.objects.all().first().id,
            'diagnosis_code': DiagnosisCode.objects.all().first().id,
            'participant_hospitalized': YES,
            'reason_hospitalized': ReasonHospitalized.objects.all().first().id,
            'days_hospitalized': 3,
            'registered_subject': self.registered_subject.id,
            'report_datetime': timezone.now(),
        }

    def test_create_model_instance(self):
        with self.assertRaises(Exception) as cm:
            try:
                DeathReport.objects.create(
                    registered_subject=self.registered_subject,
                    report_datetime=timezone.now(),
                    death_date=(timezone.now() - relativedelta(weeks=1)).date(),
                    cause=Cause.objects.all().first(),
                    cause_category=CauseCategory.objects.all().first(),
                    diagnosis_code=DiagnosisCode.objects.all().first(),
                    medical_responsibility=MedicalResponsibility.objects.all().first(),
                    illness_duration=1)
            except:
                pass
            else:
                raise Exception(cm.exception)

    def test_form_valid(self):
        form = DeathReportForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_form_validate_date_of_death_and_registration_datetime(self):
        self.data['death_date'] = timezone.now().date() - relativedelta(weeks=2)
        self.data['participant_hospitalized'] = YES
        self.data['reason_hospitalized'] = ReasonHospitalized.objects.all().first().id
        self.data['days_hospitalized'] = 1
        self.registered_subject.registration_datetime = timezone.now() - relativedelta(weeks=1)
        self.registered_subject.save()
        form = DeathReportForm(data=self.data)
        form.is_valid()
        self.assertIn(
            'Death date cannot be before date registered', form.errors.get('__all__') or [])

    def test_form_validate_date_of_death_and_dob(self):
        self.data['death_date'] = timezone.now().date() - relativedelta(years=2)
        self.data['participant_hospitalized'] = YES
        self.data['reason_hospitalized'] = ReasonHospitalized.objects.all().first().id
        self.data['days_hospitalized'] = 1
        self.registered_subject.registration_datetime = timezone.now() - relativedelta(weeks=1)
        self.registered_subject.dob = timezone.now() - relativedelta(years=1)
        self.registered_subject.save()
        form = DeathReportForm(data=self.data)
        form.is_valid()
        self.assertIn(
            'Death date cannot be before date of birth', form.errors.get('__all__') or [])

    def test_form_not_hospitalized_days_1(self):
        self.data['participant_hospitalized'] = NO
        self.data['reason_hospitalized'] = None
        self.data['days_hospitalized'] = 1
        death_report_form = DeathReportForm(data=self.data)
        self.assertIn(
            'If the participant was not hospitalized, do not indicate for how many days.',
            death_report_form.errors.get('__all__') or [])

    def test_form_not_hospitalized_days_0(self):
        self.data['participant_hospitalized'] = NO
        self.data['reason_hospitalized'] = None
        self.data['days_hospitalized'] = 0
        death_report_form = DeathReportForm(data=self.data)
        self.assertIn(
            'If the participant was not hospitalized, do not indicate for how many days.',
            death_report_form.errors.get('__all__') or [])

    def test_form_reason_hospitalized_days_none(self):
        self.data['participant_hospitalized'] = YES
        self.data['reason_hospitalized'] = ReasonHospitalized.objects.all().first().id
        self.data['days_hospitalized'] = None
        death_report_form = DeathReportForm(data=self.data)
        self.assertIn(
            'If the participant was hospitalized, indicate for how many days.',
            death_report_form.errors.get('__all__') or [])

    def test_form_reason_hospitalized_days0(self):
        self.data['participant_hospitalized'] = YES
        self.data['reason_hospitalized'] = ReasonHospitalized.objects.all().first().id
        self.data['days_hospitalized'] = 0
        death_report_form = DeathReportForm(data=self.data)
        self.assertIn(
            'If the participant was hospitalized, indicate for how many days.',
            death_report_form.errors.get('__all__') or [])

    def test_form_reason_hospitalized_days_neg(self):
        self.data['participant_hospitalized'] = YES
        self.data['reason_hospitalized'] = ReasonHospitalized.objects.all().first().id
        self.data['days_hospitalized'] = -1
        death_report_form = DeathReportForm(data=self.data)
        self.assertIn(
            'If the participant was hospitalized, indicate for how many days.',
            death_report_form.errors.get('__all__') or [])

    def test_form_reason_hospitalized_reason(self):
        self.data['participant_hospitalized'] = YES
        self.data['reason_hospitalized'] = None
        self.data['days_hospitalized'] = 1
        form = DeathReportForm(data=self.data)
        self.assertIn(
            'If the participant was hospitalized, indicate the primary reason.',
            form.errors.get('__all__'))

    def test_form_cause_other(self):
        for cause in Cause.objects.all():
            if 'other' in cause.name.lower():
                self.data['cause'] = cause.id
        form = DeathReportForm(data=self.data)
        self.assertIn(
            'You wrote \'other\' for the cause of death. Please specify.',
            form.errors.get('__all__') or [])

    def test_form_cause_other_specified(self):
        for cause in Cause.objects.all():
            if 'other' in cause.name.lower():
                self.data['cause'] = cause.id
        self.data['cause_other'] = 'an other reason'
        form = DeathReportForm(data=self.data)
        self.assertTrue(form.is_valid())