using System;
using System.IO;
using System.Text.Json;
using Microsoft.Extensions.Configuration;

namespace CalendarApp.Data
{
    public static class DataStore
    {
        private static readonly string RootPath;

        static DataStore()
        {
            var config = new ConfigurationBuilder()
                .SetBasePath(AppDomain.CurrentDomain.BaseDirectory)
                .AddJsonFile("appsettings.json", optional: true)
                .Build();

            RootPath = config["DataRoot"] ?? "data";
        }

        private static string GetFilePath(int year, int month)
        {
            string dir = Path.Combine(RootPath, year.ToString());
            Directory.CreateDirectory(dir);
            return Path.Combine(dir, $"{month:D2}.json");
        }

        public static void Save<T>(T data, int year, int month)
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(GetFilePath(year, month), JsonSerializer.Serialize(data, options));
        }

        public static T Load<T>(int year, int month)
        {
            var path = GetFilePath(year, month);
            if (File.Exists(path))
            {
                var json = File.ReadAllText(path);
                return JsonSerializer.Deserialize<T>(json);
            }
            return default;
        }
    }
}
