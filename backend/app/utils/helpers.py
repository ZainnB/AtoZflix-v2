from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, hashed):
    return check_password_hash(hashed, password)


def safe_database_uri(uri):
    """
    A DATABASE_URL with the password replaced by ***, safe to print.

    Every pipeline script banners the URI it is about to work against, which
    is genuinely useful - running an import against the wrong database is an
    easy and expensive mistake. Printing it verbatim, though, writes the
    password into terminal scrollback, CI logs and any pasted output. This
    keeps the useful part (driver, host, port, database) and drops the
    credential.
    """
    if not uri or "@" not in uri:
        return uri

    scheme, _, rest = uri.partition("://")
    if not rest:
        return uri

    # Split on the LAST "@": a password may legitimately contain one.
    credentials, _, location = rest.rpartition("@")
    if ":" not in credentials:
        return uri

    user, _, _password = credentials.partition(":")
    return f"{scheme}://{user}:***@{location}"
