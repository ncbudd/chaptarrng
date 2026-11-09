using System;
using System.Collections.Generic;
using System.Data;
using NzbDrone.Core.Configuration;

namespace NzbDrone.Core.Datastore
{
    // A synchronous unit of work shared by repositories. Connections are borrowed; only the
    // outer operation may commit. Events are published after commit, never after rollback.
    public sealed class DatabaseAtomicOperation : IDisposable
    {
        [ThreadStatic]
        private static DatabaseAtomicOperation _current;
        private readonly List<Action> _events = new List<Action>();
        private IDatabase _database;
        private IDbConnection _connection;
        private IDbTransaction _transaction;
        private bool _aborted;
        private bool _completed;

        private DatabaseAtomicOperation()
        {
            if (_current != null)
            {
                throw new InvalidOperationException("An atomic database operation is already active.");
            }

            _current = this;
        }

        public static bool IsActive => _current != null;
        public static DatabaseAtomicOperation Begin() => new DatabaseAtomicOperation();

        internal static IDbConnection OpenConnection(IDatabase database)
        {
            var operation = _current;
            if (operation == null)
            {
                return database.OpenConnection();
            }

            if (operation._database != null && !ReferenceEquals(operation._database, database))
            {
                throw new InvalidOperationException("An atomic operation cannot span different databases.");
            }

            if (operation._connection == null)
            {
                operation._database = database;
                operation._connection = database.OpenConnection();
                operation._transaction = operation._connection.BeginTransaction(IsolationLevel.Serializable);
            }

            return new BorrowedConnection(operation);
        }

        public static bool DeferEvent(Action publish)
        {
            if (_current == null)
            {
                return false;
            }

            _current._events.Add(publish);
            return true;
        }

        public void Complete()
        {
            if (_aborted)
            {
                throw new InvalidOperationException("A nested repository operation failed; the transaction cannot commit.");
            }

            _transaction?.Commit();
            _completed = true;
            _current = null;
            ConfigService.InvalidateCache();
            foreach (var publish in _events)
            {
                publish();
            }
        }

        public void Dispose()
        {
            try
            {
                if (!_completed)
                {
                    _transaction?.Rollback();
                }
            }
            finally
            {
                _current = null;
                _transaction?.Dispose();
                _connection?.Dispose();
                ConfigService.InvalidateCache();
            }
        }

        private sealed class BorrowedConnection : IDbConnection
        {
            private readonly DatabaseAtomicOperation _owner;
            public BorrowedConnection(DatabaseAtomicOperation owner) { _owner = owner; }
            public string ConnectionString { get => _owner._connection.ConnectionString; set => throw new NotSupportedException(); }
            public int ConnectionTimeout => _owner._connection.ConnectionTimeout;
            public string Database => _owner._connection.Database;
            public ConnectionState State => _owner._connection.State;
            public IDbTransaction BeginTransaction() => new BorrowedTransaction(_owner, this);
            public IDbTransaction BeginTransaction(IsolationLevel isolationLevel) => BeginTransaction();
            public void ChangeDatabase(string databaseName) => throw new NotSupportedException();
            public void Close() { }
            public void Open() { }
            public void Dispose() { }
            public IDbCommand CreateCommand() => new BorrowedCommand(_owner._connection.CreateCommand(), _owner, this);
        }

        private sealed class BorrowedTransaction : IDbTransaction
        {
            private readonly DatabaseAtomicOperation _owner;
            private bool _completed;
            public BorrowedTransaction(DatabaseAtomicOperation owner, IDbConnection connection) { _owner = owner; Connection = connection; }
            public IDbConnection Connection { get; }
            public IsolationLevel IsolationLevel => _owner._transaction.IsolationLevel;
            public void Commit() { _completed = true; }
            public void Rollback() { _owner._aborted = true; _completed = true; }
            public void Dispose() { if (!_completed) { _owner._aborted = true; } }
        }

        private sealed class BorrowedCommand : IDbCommand
        {
            private readonly IDbCommand _inner;
            private readonly DatabaseAtomicOperation _owner;
            public BorrowedCommand(IDbCommand inner, DatabaseAtomicOperation owner, IDbConnection connection)
            {
                _inner = inner;
                _owner = owner;
                Connection = connection;
                _inner.Transaction = owner._transaction;
            }

            // nosemgrep: csharp.lang.security.sqli.csharp-sqli.csharp-sqli -- This method delegates to the already parameterized database command; it does not construct or interpolate SQL.
            public string CommandText { get => _inner.CommandText; set => _inner.CommandText = value; }
            public int CommandTimeout { get => _inner.CommandTimeout; set => _inner.CommandTimeout = value; }
            public CommandType CommandType { get => _inner.CommandType; set => _inner.CommandType = value; }
            public IDbConnection Connection { get; set; }
            public IDataParameterCollection Parameters => _inner.Parameters;
            public IDbTransaction Transaction { get => _owner._transaction; set => _inner.Transaction = _owner._transaction; }
            public UpdateRowSource UpdatedRowSource { get => _inner.UpdatedRowSource; set => _inner.UpdatedRowSource = value; }
            public void Cancel() => _inner.Cancel();
            public IDbDataParameter CreateParameter() => _inner.CreateParameter();
            public int ExecuteNonQuery() => _inner.ExecuteNonQuery();
            public IDataReader ExecuteReader() => _inner.ExecuteReader();
            public IDataReader ExecuteReader(CommandBehavior behavior) => _inner.ExecuteReader(behavior & ~CommandBehavior.CloseConnection);
            public object ExecuteScalar() => _inner.ExecuteScalar();
            public void Prepare() => _inner.Prepare();
            public void Dispose() => _inner.Dispose();
        }
    }
}
