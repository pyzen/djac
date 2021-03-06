import decimal
from datetime import date, timedelta

from django.db import models

from accounts.models import Account, Journal, Posting


class AutoBudget(models.Model):
    delta = models.DecimalField(max_digits=14, decimal_places=2,
	default=decimal.Decimal('86400.0'))
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2,
	default=decimal.Decimal('0.00'))
    payer = models.ForeignKey(Account, related_name='+')
    payee = models.ForeignKey(Account, related_name='+')


class Budget(models.Model):
    date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=14, decimal_places=2,
	default='0.00')
    payer = models.ForeignKey(Account, related_name='+')
    payee = models.ForeignKey(Account, related_name='+')
    journal = models.ForeignKey(Journal, null=True)
    is_applied = models.BooleanField(default=False)
    auto_budget = models.ForeignKey(AutoBudget, null=True)

    def __unicode__(self):
	return "%s, %s, from %s to %s" % (self.date, self.amount,
	    self.payer.name, self.payee.name)

    def save(self, *args, **kwargs):
	if (self.is_applied and self.journal is None):
	    payer = self.payer
            payee = self.payee
            if (payer.userprofile_set.exists() and
                payee.userprofile_set.exists()):
                journal = Journal.objects.create(type="Transfer")
            elif payer.userprofile_set.exists():
                journal = Journal.objects.create(type="Expense")
            elif payee.userprofile_set.exists():
                journal = Journal.objects.create(type="Income")

            credit_amt = self.amount.to_eng_string()
            debit_amt = '-' + credit_amt

            self.journal = journal
            credit = Posting.objects.create(date=self.date,
                journal=self.journal, amount=credit_amt, account=self.payee)
            debit = Posting.objects.create(date=self.date, journal=self.journal,
                amount=debit_amt, account=self.payer)


	elif (not self.is_applied and self.journal is not None):
	    Posting.objects.filter(journal=self.journal).delete()
	    self.journal = None

	super(Budget, self).save(*args, **kwargs)


