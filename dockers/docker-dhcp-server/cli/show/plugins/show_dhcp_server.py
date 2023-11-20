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
@click.argument("option_name", required=False)
@clicommon.pass_db
def option(db, option_name):
    if not option_name:
        option_name = "*"
    headers = ["Option Name", "Option", "Value", "Type"]
    table = []
    dbconn = db.db
    for key in dbconn.keys("CONFIG_DB", "DHCP_SERVER_IPV4_CUSTOMIZED_OPTIONS|" + option_name):
        entry = dbconn.get_all("CONFIG_DB", key)
        name = key.split("|")[1]
        table.append([name, entry["id"], entry["value"], entry["type"]])
    print(tabulate(table, headers=headers))


def register(cli):
    cli.add_command(dhcp_server)
