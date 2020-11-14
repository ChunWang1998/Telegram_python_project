from django.utils import timezone


class BotMixin:

    @staticmethod
    def get_dates(request):
        """

        The method will extract the start_date strings from request params and convert them to python datetime

        :param request: django request
        :return:
        """
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)

        if start_date and end_date:
            start_date = timezone.make_aware(timezone.datetime.strptime(start_date, "%d/%m/%Y"))
            end_date = timezone.make_aware(timezone.datetime.strptime(end_date, "%d/%m/%Y"))

        else:

            # if no default start date ad end date
            now = timezone.now()
            start_date = timezone.datetime(day=1, month=now.month, year=now.year)
            end_date = timezone.now()

        return start_date, end_date + timezone.timedelta(days=1)
