import sys
from colink import (
    CoLink,
    get_time_stamp,
    generate_user,
    prepare_import_user_signature,
    decode_jwt_without_validation,
)

if __name__ == "__main__":
    addr = "http://127.0.0.1:2021"
    core_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwcml2aWxlZ2UiOiJob3N0IiwidXNlcl9pZCI6IjAyYjU4MTNmOWU1MGJlNDlhM2FmYzA2NWNiNjQ5NmQ1NjMyN2I4YzcwY2ZmODU5MWE4OTk5MjgwNTQ5YThjZTgzZCIsImV4cCI6MTcwOTIwNDIxN30.mAFhA0vPB1IeU2jbXsiAeO-yVLhkdNYeMKdP2WDJLMY"

    expiration_timestamp = get_time_stamp() + 86400 * 31

    cl = CoLink(addr, core_jwt)

    num = 2

    users = []
    for i in range(num):
        pub_key, sec_key = generate_user()
        core_pub_key = cl.request_info().core_public_key
        signature_timestamp, sig = prepare_import_user_signature(
            pub_key, sec_key, core_pub_key, expiration_timestamp
        )
        jwt = cl.import_user(pub_key, signature_timestamp, expiration_timestamp, sig)
        users.append(jwt)

    for i in range(num):
        for j in range(num):
            if i != j:
                cl = CoLink(addr, users[i])
                cl.import_guest_jwt(users[j])  # for auth
                jwt = decode_jwt_without_validation(users[j])
                cl.import_core_addr(jwt.user_id, addr)  # for contact

    with open("jwts.txt", "w") as file:
        for i in range(num):
            file.write(str(users[i]) + "\n")
            print(f"user {i}", decode_jwt_without_validation(users[i]).user_id)
