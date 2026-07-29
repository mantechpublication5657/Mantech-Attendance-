from django import forms
from .models import Payroll


class PayrollForm(forms.ModelForm):

    class Meta:
        model = Payroll

        fields = [
            "gross_salary",
            "basic_salary",
            "hra",
            "da",
            "bonus",
            "bonus_remark",
            "deductions",
            "deduction_remark",
        ]
        
        labels = {
            "hra": "HRA",
            "da": "SA",
            "bonus_remark": "Bonus Remark",
            "deduction_remark": "Deduction Remark",
        }

        widgets = {
            "gross_salary": forms.NumberInput(
                attrs={"step": "0.01","placeholder": "Ex: Gross Salary..."}
            ),
            "basic_salary": forms.NumberInput(
                attrs={"step": "0.01","placeholder": "Ex: Basic Salary..."}
            ),
            "hra": forms.NumberInput(
                attrs={"step": "0.01","placeholder": "Ex: House Rent Allowance/Any Other Expenses..."}
            ),
            "da": forms.NumberInput(
                attrs={"step": "0.01","placeholder": "Ex: Special Allowance/Any Other allowances..."}
            ),
            "bonus": forms.NumberInput(
                attrs={"step": "0.01","placeholder": "Ex: Diwali/Holi Bonus/Any Other Bonuses..."}
            ),
            "deductions": forms.NumberInput(
                attrs={"step": "0.01", "placeholder": "Ex: Advanced Salary/Any Other Deductions..."}
            ),
            "bonus_remark": forms.TextInput(
                attrs={"placeholder": "Reason for bonus..."}
            ),
            "deduction_remark": forms.TextInput(
                attrs={"placeholder": "Reason for deduction..."}
            ),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # NOT REQUIRED — will be filled from previous month if empty
        self.fields["gross_salary"].required = False
        self.fields["basic_salary"].required = False
        self.fields["hra"].required = False
        self.fields["da"].required = False

    def save(self, commit=True):
        payroll = super().save(commit=False)
        if commit:
            payroll.save()
        return payroll