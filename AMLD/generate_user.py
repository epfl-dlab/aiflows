from colink import (
    CoLink,
    get_time_stamp,
    generate_user,
    prepare_import_user_signature,
)


if __name__ == "__main__":
    addr = "https://amld.colink-server.colearn.cloud"
    cl = CoLink(addr, "")

    pub_key, sec_key = generate_user()

    core_pub_key = cl.request_info().core_public_key

    expiration_timestamp = get_time_stamp() + 86400 * 31
    signature_timestamp, sig = prepare_import_user_signature(
        pub_key, sec_key, core_pub_key, expiration_timestamp
    )

    with open("user.txt", "w") as file:
        file.write(f"pub_key: {pub_key.format(compressed=True).hex()}\n")
        file.write(f"expiration_timestamp: {expiration_timestamp}\n")
        file.write(f"signature_timestamp: {signature_timestamp}\n")
        file.write(f"sig: {sig.hex()}\n")

    print(
        "Created colink user. Please share the generated user.txt file with the server admin."
    )
