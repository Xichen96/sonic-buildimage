import click
import utilities_common.cli as clicommon


SUPPORT_TYPE = ["binary", "boolean", "ipv4-address", "string", "uint8", "uint16", "uint32"]


def validate_str_type(type, value):
    """
    To validate whether type is consistent with string value
    Args:
        type: string, value type
        value: checked value
    Returns:
        True, type consistent with value
        False, type not consistent with value
    """
    if not isinstance(value, str):
        return False
    if type not in SUPPORT_TYPE:
        return False
    if type == "string":
        return True
    if type == "binary":
        if len(value) == 0 or len(value) % 2 != 0:
            return False
        return all(c in set(string.hexdigits) for c in value)
    if type == "boolean":
        return value in ["true", "false"]
    if type == "ipv4-address":
        try:
            if len(value.split(".")) != 4:
                return False
            return ipaddress.ip_address(value).version == 4
        except ValueError:
            return False
    if type.startswith("uint"):
        if not value.isdigit():
            return False
        length = int("".join([c for c in type if c.isdigit()]))
        return 0 <= int(value) <= int(pow(2, length)) - 1
    return False


@click.group(cls=clicommon.AbbreviationGroup, name="dhcp_server")
def dhcp_server():
    """config DHCP Server information"""
    ctx = click.get_current_context()
    dbconn = db.db
    if dbconn.get("CONFIG_DB", "FEATURE|dhcp_server", "state") != "enabled":
        ctx.fail("Feature dhcp_server is not enabled")


@dhcp_server.group(cls=clicommon.AliasedGroup, name="ipv4")
def dhcp_server_ipv4():
    """Show ipv4 related dhcp_server info"""
    pass


@ipv4.command(name="add")
@click.argument("dhcp_interface", required=True)
@click.option("--mode", required=True)
@click.option("--lease_time", required=False, default="900")
@click.option("--dup_gw_nm", required=False, default=False, is_flag=True)
@click.option("--gateway", required=False)
@click.option("--netmask", required=False)
@clicommon.pass_db
def dhcp_server_ipv4_add(db, mode, lease_time, dup_gw_nm, gateway, netmask, dhcp_interface):
    ctx = click.get_current_context()
    if mode != "PORT":
        ctx.fail("Only mode PORT is supported")
    if not validate_str_type("uint32", lease_time):
        ctx.fail("lease_time is required and must be nonnegative integer")
    dbconn = db.db
    if dbconn.exists("CONFIG_DB", "VLAN_INTERFACE|" + dhcp_interface):
        ctx.fail("dhcp_interface {} does not exist".format(dhcp_interface))
    if dup_gw_nm:
        dup_success = False
        for key in dbconn.keys("CONFIG_DB", "VLAN_INTERFACE|" + dhcp_interface + "|*"):
            network = ipaddress.ip_network(key.lstrip("VLAN_INTERFACE|" + dhcp_interface + "|"))
            if network.version != 4:
                continue
            dup_success = True
            gateway, netmask = network.ip, network.netmask
        if not dup_success:
            ctx.fail("failed to found gateway and netmask for Vlan interface {}".format(dhcp_interface))
    elif not validate_str_type("ipv4-address", gateway) or validate_str_type("ipv4-address", netmask):
            ctx.fail("gateway and netmask must be valid ipv4 string")
    key = "DHCP_SERVER_IPV4|" + dhcp_interface
    if dbconn.exists("CONFIG_DB", key):
        ctx.fail("Dhcp_interface %s already exist".format(dhcp_interface))
    else:
        dbconn.hmset("CONFIG_DB", key, {
            "mode": mode,
            "lease_time": lease_time,
            "gateway": gateway,
            "netmask": netmask,
            "state": "disabled",
            })


def register(cli):
    # cli.add_command(dhcp_server)
    pass


if __name__ == '__main__':
    dhcp_server()
