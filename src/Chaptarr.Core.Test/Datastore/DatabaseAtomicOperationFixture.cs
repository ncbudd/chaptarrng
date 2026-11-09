using System;
using System.IO;
using Dapper;
using Microsoft.Data.Sqlite;
using NUnit.Framework;
using NzbDrone.Core.Datastore;

namespace Chaptarr.Core.Test.Datastore
{
    [TestFixture]
    public class DatabaseAtomicOperationFixture
    {
        [TestCase(false)]
        [TestCase(true)]
        public void multiple_repository_connections_and_nested_transactions_commit_or_rollback_together(bool complete)
        {
            var path = Path.Combine(Path.GetTempPath(), Guid.NewGuid() + ".db");
            var database = new MainDatabase(new Database("test", () =>
            {
                var connection = new SqliteConnection("Data Source=" + path + ";Pooling=False");
                connection.Open();
                return connection;
            }));
            try
            {
                using (var setup = database.OpenConnection()) { setup.Execute("CREATE TABLE Changes (Id INTEGER);"); }
                var published = false;
                using (var operation = DatabaseAtomicOperation.Begin())
                {
                    using (var first = database.OpenConnection()) { first.Execute("INSERT INTO Changes VALUES (1);"); }
                    using (var second = database.OpenConnection())
                    using (var nested = second.BeginTransaction())
                    {
                        second.Execute("INSERT INTO Changes VALUES (2);", transaction: nested);
                        nested.Commit();
                    }

                    DatabaseAtomicOperation.DeferEvent(() => published = true);
                    Assert.That(published, Is.False);
                    if (complete) { operation.Complete(); }
                }

                using var check = database.OpenConnection();
                Assert.That(check.ExecuteScalar<int>("SELECT COUNT(*) FROM Changes"), Is.EqualTo(complete ? 2 : 0));
                Assert.That(published, Is.EqualTo(complete));
            }
            finally { File.Delete(path); }
        }
    }
}
