import math
import numpy as np
import pandas as pd
import prettytable as pt
import matplotlib.pyplot as plt


def IRyearly2monthly(yearly_rate):
    yearly_rate /= 1e2
    monthly_rate = (1 + yearly_rate) ** (1 / 12) - 1
    return monthly_rate*1e2


def calMonthlyCI(principal, monthly_rate, months):
    monthly_rate /= 1e2
    total_amount = principal * (1 + monthly_rate)**months
    return total_amount


class LoanParams(object):
    def __init__(self, in_principal, in_rate, in_month, month_bias=0, loan_name="loan", loan_type="等额本息"):
        self.loan_name = loan_name
        self.loan_type = loan_type
        self.total_principal = in_principal
        self.total_payment = 0
        self.total_interest = 0

        self.month_bias = month_bias
        self.periods = []
        init_period = {"node": 1, "rate": in_rate, "month": in_month, "principal_acc": 0, "pre_payment": 0, "income": 0}
        self.periods.append(init_period)
        self.monthly_bill = pd.DataFrame(columns=["time", "payment", "principal", "interest", "principal_rest"])

    def getPeriodPrincipalRest(self, period_num):
        pay_principal = 0
        for i in range(period_num + 1):
            period = self.periods[i]
            pay_principal += (period["principal_acc"])
        principal_rest = self.total_principal - pay_principal - self.periods[period_num]["pre_payment"]
        return principal_rest

    def setPeriodChange(self, node_month, fix_rate=math.nan, fix_month=math.nan, pre_payment=math.nan, income=0):
        if math.isnan(fix_rate) and math.isnan(fix_month) and math.isnan(pre_payment) or node_month > fix_month:
            print("无用的贷款参数修改")
            return
        pre_period = self.periods[-1]
        curr_period = pre_period.copy()
        curr_period["node"] = node_month
        curr_period["income"] = income
        curr_period["principal_acc"] = 0
        if not math.isnan(fix_rate):
            curr_period["rate"] = fix_rate
        if not math.isnan(fix_month):
            curr_period["month"] = fix_month
        if not math.isnan(pre_payment):
            curr_period["pre_payment"] = pre_payment
        self.periods.append(curr_period)

    def printLoanParams(self):
        """贷款选项信息"""
        print("\n", "=" * 20, self.loan_name, "=" * 20)
        print("贷款方式: ", self.loan_type)
        print("贷款金额: ￥", self.total_principal)
        loan_params_info = pt.PrettyTable()
        loan_params_info.field_names = ["start (month)", "rate (%)",
                                        "time (month)", "PrePayment (￥)", "income (￥)"]
        for period in self.periods:
            loan_params_info.add_row([period["node"], period["rate"], period["month"], period["pre_payment"], period["income"]])

        loan_params_info.float_format = ".2"
        print(loan_params_info)


def printMonthlyTable(pd_table):
    """输出月度表格"""
    table = pt.PrettyTable()
    table.field_names = pd_table.columns
    for idx, row in pd_table.iterrows():
        table.add_row(row)
    table.float_format = ".2"
    print(table)


class LoanCalculater(object):
    def __init__(self):
        self.total_bill = pd.DataFrame(columns=["month", "payment", "principal", "interest", "principal_rest"])

    @staticmethod
    def equalInterest(params: LoanParams):
        """等额本息"""
        for period in range(len(params.periods)):
            curr_period = params.periods[period]
            period_srt_month = curr_period["node"]
            period_end_month = curr_period["month"]
            if period != len(params.periods) - 1:
                period_end_month = params.periods[period + 1]["node"] - 1
            month_rest = curr_period["month"] - period_srt_month + 1  # 剩余总月数, 当月也是本周期内
            principal_rest = params.getPeriodPrincipalRest(period)  # 剩余总本金
            rate_m = curr_period["rate"] / 1200  # 月利率
            payment_m = (principal_rest * rate_m * (1 + rate_m) ** month_rest) / ((1 + rate_m) ** month_rest - 1)
            period_principal_acc = 0
            # print(principal_rest, payment_m)
            for time_num in range(1, period_end_month - period_srt_month + 2):
                principal_m = (principal_rest * rate_m * (1 + rate_m) ** (time_num - 1)) / (
                        (1 + rate_m) ** month_rest - 1)
                interest_m = payment_m - principal_m
                income = 0
                pre_payment = 0
                if time_num == 1:
                    pre_payment = curr_period["pre_payment"]
                    income = curr_period["income"]
                period_principal_acc += principal_m

                time = period_srt_month + time_num - 1
                params.monthly_bill.at[time - 1, "time"] = time
                params.monthly_bill.at[time - 1, "payment"] = payment_m + pre_payment - income
                params.monthly_bill.at[time - 1, "principal"] = principal_m + pre_payment  - income
                params.monthly_bill.at[time - 1, "interest"] = interest_m
                params.monthly_bill.at[time - 1, "principal_rest"] = principal_rest - period_principal_acc
                curr_period["principal_acc"] = period_principal_acc + curr_period["pre_payment"]

        params.total_payment = params.monthly_bill["payment"].sum()
        params.total_interest = params.monthly_bill["interest"].sum()

    def equal_principal(self, P, R, N):
        """等额本金"""
        B = P / N
        for i in range(1, N + 1):
            A = P / N + (P - P / N * (i - 1)) * R / 1200
            r = A - B
            installment_dict = {"time_num": i,
                                "monthly_payment": round(A, 2),
                                "monthly_principal": round(B, 2),
                                "monthly_interest": round(r, 2),
                                "rest_loan": round(P - P / N * i, 2)}
            self.installment_list.append(installment_dict)
        self.total_payment = (round(sum([x["monthly_payment"] for x in self.installment_list])))
        self.total_interest = (round(sum([x["monthly_interest"] for x in self.installment_list])))

    def loanCalculation(self, *loan_params: LoanParams, single_table=False, total_table=True):
        """计算结果显示"""
        for param in loan_params:
            if param.loan_type == "等额本息":
                param.printLoanParams()
                self.equalInterest(param)
            # elif params.loan_type == "等额本金":
            #     self.equal_principal(P, R, N)
            if single_table:
                printMonthlyTable(param.monthly_bill)
                print("总还款: {:.2f}, 总利息: {:.2f}".format(param.total_payment, param.total_interest))

            for idx, time_info in param.monthly_bill.iterrows():
                month = time_info["time"] + param.month_bias
                monthly_bill = time_info.copy()
                monthly_bill["month"] = month
                if not np.any(self.total_bill['month'].isin([month]).values):
                    self.total_bill.at[month - 1] = monthly_bill.copy()
                else:
                    self.total_bill.at[month - 1, "payment"] += monthly_bill["payment"]
                    self.total_bill.at[month - 1, "interest"] += monthly_bill["interest"]
                    self.total_bill.at[month - 1, "principal"] += monthly_bill["principal"]
                    self.total_bill.at[month - 1, "principal_rest"] += monthly_bill["principal_rest"]

        self.total_bill = self.total_bill.sort_values('month')
        total_payment = self.total_bill["payment"].sum()
        total_interest = self.total_bill["interest"].sum()
        total_principal = self.total_bill["principal"].sum()
        print("\n", "=" * 20, "总账单", "=" * 20)
        if total_table:
            printMonthlyTable(self.total_bill)
        print("总贷款: {:.2f}, 总还款: {:.2f}, 总利息: {:.2f}".format(total_principal, total_payment, total_interest))

    def getClipWithinPeriod(self, start_month, end_month):
        bill_clip = self.total_bill[(self.total_bill["month"] >= start_month) &
                                    (self.total_bill["month"] <= end_month)].copy()
        bill_clip = bill_clip[["payment", "principal", "interest"]].copy()
        bill_clip = bill_clip.astype(float).astype(int)
        return bill_clip

    def statisticPlot(self):
        # plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体
        # plt.rcParams["axes.unicode_minus"] = False  # 该语句解决图像中的“-”负号的乱码问题

        plt.figure(figsize=(12, 8))
        plt.title('monthly analyze')
        plt.plot(self.total_bill["month"], self.total_bill["payment"])
        plt.plot(self.total_bill["month"], self.total_bill["principal"])
        plt.plot(self.total_bill["month"], self.total_bill["interest"])
        plt.legend(["payment", "principal", "interest"])
        plt.xlabel("month")
        plt.ylabel("yuan")
        plt.grid()

        plt.figure(figsize=(12, 8))
        plt.title('total analyze')
        plt.plot(self.total_bill["month"], self.total_bill["principal_rest"])
        plt.legend(["principal_rest"])
        plt.xlabel("month")
        plt.ylabel("yuan")
        plt.grid()
        plt.show()

    def loanStatistic(self):
        fund_loan = LoanParams(120*1e4, 3.25, 25*12, loan_name="公积金贷款")
        fund_loan.setPeriodChange(13, fix_rate=3.10)

        business_loan = LoanParams(183*1e4, 4.65 + 0.55, 25*12, loan_name="商业贷款")
        business_loan.setPeriodChange(12, fix_rate=4.3 + 0.55)
        # business_loan.setPeriodChange(21, pre_payment=10*1e4, fix_month=23*12-3)
        business_loan.setPeriodChange(21, pre_payment=10*1e4, income=10*1e4)

        # business_loan.setPeriodChange(21, pre_payment=10*1e4)
        business_loan.setPeriodChange(24, fix_rate=4.2 + 0.55, pre_payment=0)

        person_loan = LoanParams(10*1e4, 3.6, 36, loan_name="消费贷款", month_bias=21)
        self.loanCalculation(fund_loan, business_loan, person_loan, single_table=False, total_table=False)
        # self.statisticPlot()
        bill_clip = self.getClipWithinPeriod(1, 65)
        print(bill_clip.sum())

if __name__ == '__main__':
    loan = LoanCalculater()
    loan.loanStatistic()

   