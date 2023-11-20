import click
from tabulate import tabulate
import utilities_common.cli as clicommon


import ipaddress
from datetime import datetime


def ts_to_str(ts):
    return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")


@click.group(cls=clicommon.AliasedGroup)
def dhcp_server():
    """Show dhcp_server related info"""
    pass


@dhcp_server.group(cls=clicommon.AliasedGroup)
def ipv4():
    """Show ipv4 related dhcp_server info"""
    pass


@ipv4.command()
@click.argument('dhcp_interface', required=False)
@clicommon.pass_db
def lease(db, dhcp_interface):
    if not dhcp_interface:
        dhcp_interface = "*"
    headers = ["Interface", "MAC Address", "IP", "Lease Start", "Lease End"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("STATE_DB", "DHCP_SERVER_IPV4_LEASE|" + dhcp_interface + "|*"):
        entry = dbconn.get_all("STATE_DB", key)
        interface, mac = key.split("|")[1:]
        port = dbconn.get("STATE_DB", "FDB_TABLE|" + interface + ":" + mac, "port")
        if not port:
            port = "<Unknown>"
        table.append([interface + "|" + port, mac, entry["ip"], ts_to_str(entry["lease_start"]), ts_to_str(entry["lease_end"])])
    click.echo(tabulate(table, headers=headers))


@ipv4.command()
@click.argument('dhcp_interface', required=False)
@click.option('--with_customized_options', default=False, is_flag=True)
@clicommon.pass_db
def info(db, dhcp_interface, with_customized_options):
    if not dhcp_interface:
        dhcp_interface = "*"
    headers = ["Interface", "Mode", "Gateway", "Netmask", "Lease Time(s)", "IP Bind"]
    if with_customized_options:
        headers.append("Customize Option")
    table = []
    dbconn = db.db
    for key in dbconn.keys("CONFIG_DB", "DHCP_SERVER_IPV4|" + dhcp_interface):
        entry = dbconn.get_all("CONFIG_DB", key)
        interface = key.split("|")[1]
        table.append([interface, entry["mode"], entry["gateway"], entry["netmask"], entry["lease_time"], entry["state"]])
        if with_customize_option:
            table[-1].append(entry["customized_options"])
    print(tabulate(table, headers=headers))


def register(cli):
    cli.add_command(dhcp_server)
