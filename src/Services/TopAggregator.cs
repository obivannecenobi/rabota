using System.Collections.Generic;
using System.Linq;
using CalendarApp.ViewModels;

namespace CalendarApp.Services
{
    public static class TopAggregator
    {
        public enum Period
        {
            Quarter,
            HalfYear,
            Year,
            Custom
        }

        public enum SortMetric
        {
            Profit,
            Views
        }

        public static IEnumerable<TopMonthViewModel.ReportSummary> Aggregate(
            IEnumerable<TopMonthViewModel.MonthSummary> source,
            Period period,
            SortMetric sortBy = SortMetric.Profit,
            bool descending = true,
            int? startMonth = null,
            int? endMonth = null)
        {
            if (source == null)
            {
                return Enumerable.Empty<TopMonthViewModel.ReportSummary>();
            }

            IEnumerable<TopMonthViewModel.ReportSummary> result = period switch
            {
                Period.Quarter => source
                    .GroupBy(m => (m.Month - 1) / 3 + 1)
                    .Select(g => new TopMonthViewModel.ReportSummary
                    {
                        Period = $"Q{g.Key}",
                        Profit = g.Sum(x => x.Profit),
                        Views = g.Sum(x => x.Views)
                    }),
                Period.HalfYear => source
                    .GroupBy(m => (m.Month - 1) / 6 + 1)
                    .Select(g => new TopMonthViewModel.ReportSummary
                    {
                        Period = $"H{g.Key}",
                        Profit = g.Sum(x => x.Profit),
                        Views = g.Sum(x => x.Views)
                    }),
                Period.Year => new[]
                    {
                        new TopMonthViewModel.ReportSummary
                        {
                            Period = "Year",
                            Profit = source.Sum(x => x.Profit),
                            Views = source.Sum(x => x.Views)
                        }
                    },
                _ => source
                    .Where(m => m.Month >= (startMonth ?? 1) && m.Month <= (endMonth ?? 12))
                    .GroupBy(_ => 1)
                    .Select(g => new TopMonthViewModel.ReportSummary
                    {
                        Period = $"{startMonth ?? 1:D2}-{endMonth ?? 12:D2}",
                        Profit = g.Sum(x => x.Profit),
                        Views = g.Sum(x => x.Views)
                    })
            };

            result = sortBy switch
            {
                SortMetric.Views => descending
                    ? result.OrderByDescending(r => r.Views)
                    : result.OrderBy(r => r.Views),
                _ => descending
                    ? result.OrderByDescending(r => r.Profit)
                    : result.OrderBy(r => r.Profit)
            };

            return result;
        }
    }
}

