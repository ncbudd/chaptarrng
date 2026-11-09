using System;
using System.Data;
using System.Data.Common;
using System.IO;
using Dapper;
using Microsoft.Data.Sqlite;
using Npgsql;
using NUnit.Framework;
using NzbDrone.Core.Datastore;

namespace Chaptarr.Core.Test.Datastore
{
    [TestFixture]
    public class DatabaseAtomicOperationFixture
    {
        private string _path;
        private string _schema;
        private string _postgresBase;
        private string _connectionString;
        private MainDatabase _database;
        protected virtual DatabaseType Backend => DatabaseType.SQLite;

        [SetUp]
        public void SetUp()
        {
            _schema = null;
            _path = null;
            if (Backend == DatabaseType.PostgreSQL)
            {
                _postgresBase = Environment.GetEnvironmentVariable("CHAPTARRNG_POSTGRES_TEST_CONNECTION");
                if (string.IsNullOrWhiteSpace(_postgresBase))
                {
                    Assert.Ignore("Set CHAPTARRNG_POSTGRES_TEST_CONNECTION to exercise PostgreSQL atomic operations.");
                }

                using var admin = new NpgsqlConnection(_postgresBase);
                admin.Open();
                var schema = "atomic_" + Guid.NewGuid().ToString("N");
                admin.Execute("CREATE SCHEMA \"" + schema + "\"");
                _schema = schema;
                _connectionString = new NpgsqlConnectionStringBuilder(_postgresBase) { SearchPath = schema, Pooling = false }.ConnectionString;
            }
            else
            {
                _path = Path.Combine(TestContext.CurrentContext.WorkDirectory, "atomic-" + Guid.NewGuid() + ".db");
                _connectionString = new SqliteConnectionStringBuilder { DataSource = _path, Pooling = false }.ConnectionString;
            }

            _database = new MainDatabase(new Database("test", Open));
            using var setup = _database.OpenConnection();
            setup.Execute("CREATE TABLE Changes (Id INTEGER PRIMARY KEY);");
        }

        private IDbConnection Open()
        {
            IDbConnection connection = Backend == DatabaseType.PostgreSQL
                ? new NpgsqlConnection(_connectionString)
                : new SqliteConnection(_connectionString);
            connection.Open();
            return connection;
        }

        [TearDown]
        public void TearDown()
        {
            if (_schema != null)
            {
                using var admin = new NpgsqlConnection(_postgresBase);
                admin.Open();
                admin.Execute("DROP SCHEMA \"" + _schema + "\" CASCADE");
                _schema = null;
            }

            if (_path != null) { File.Delete(_path); }
        }

        [TestCase(false)]
        [TestCase(true)]
        public void multiple_repository_connections_and_nested_transactions_commit_or_rollback_together(bool complete)
        {
            var published = false;
            using (var operation = DatabaseAtomicOperation.Begin())
            {
                using (var first = _database.OpenConnection()) { first.Execute("INSERT INTO Changes VALUES (1);"); }
                using (var second = _database.OpenConnection())
                using (var nested = second.BeginTransaction())
                {
                    second.Execute("INSERT INTO Changes VALUES (2);", transaction: nested);
                    nested.Commit();
                }

                DatabaseAtomicOperation.DeferEvent(() => published = true);
                Assert.That(published, Is.False);
                if (complete) { operation.Complete(); }
            }

            using var check = _database.OpenConnection();
            Assert.That(check.ExecuteScalar<int>("SELECT COUNT(*) FROM Changes"), Is.EqualTo(complete ? 2 : 0));
            Assert.That(published, Is.EqualTo(complete));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void nested_rollback_or_abandoned_transaction_prevents_outer_commit(bool explicitRollback)
        {
            var published = false;
            using (var operation = DatabaseAtomicOperation.Begin())
            {
                using (var first = _database.OpenConnection()) { first.Execute("INSERT INTO Changes VALUES (1);"); }
                using (var second = _database.OpenConnection())
                using (var nested = second.BeginTransaction())
                {
                    second.Execute("INSERT INTO Changes VALUES (2);", transaction: nested);
                    if (explicitRollback) { nested.Rollback(); }
                }

                DatabaseAtomicOperation.DeferEvent(() => published = true);
                Assert.Throws<InvalidOperationException>(() => operation.Complete());
            }

            using var check = _database.OpenConnection();
            Assert.That(check.ExecuteScalar<int>("SELECT COUNT(*) FROM Changes"), Is.Zero);
            Assert.That(published, Is.False);
            Assert.That(DatabaseAtomicOperation.IsActive, Is.False);
        }

        [Test]
        public void failed_database_write_rolls_back_prior_writes_without_publishing_events()
        {
            var published = false;
            Assert.Catch<DbException>(() =>
            {
                using var operation = DatabaseAtomicOperation.Begin();
                using (var first = _database.OpenConnection()) { first.Execute("INSERT INTO Changes VALUES (1);"); }
                DatabaseAtomicOperation.DeferEvent(() => published = true);
                using (var second = _database.OpenConnection()) { second.Execute("INSERT INTO Changes VALUES (1);"); }
                operation.Complete();
            });

            using var check = _database.OpenConnection();
            Assert.That(check.ExecuteScalar<int>("SELECT COUNT(*) FROM Changes"), Is.Zero);
            Assert.That(published, Is.False);
            Assert.That(DatabaseAtomicOperation.IsActive, Is.False);
        }
    }

    [TestFixture]
    public class PostgresDatabaseAtomicOperationFixture : DatabaseAtomicOperationFixture
    {
        protected override DatabaseType Backend => DatabaseType.PostgreSQL;
    }
}
