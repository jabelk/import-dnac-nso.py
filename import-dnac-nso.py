import ncs

from dnacentersdk import api
import urllib3
urllib3.disable_warnings()
 
dnac = api.DNACenterAPI(base_url='https://10.10.20.85:443', version='1.3.0')
dnac_device_list = dnac.devices.get_device_list(family="Switches and Hubs").get("response")

for device in dnac_device_list:
    hostname = device.get("hostname")
    mgmt_ip = device.get("managementIpAddress")
    print(hostname + " " + mgmt_ip)
    if "Host" in hostname:
        continue
    with ncs.maapi.Maapi() as m:
        with ncs.maapi.Session(m, 'admin', 'python'):
            with m.start_write_trans() as t:
                root = ncs.maagic.get_root(t)

                print("Setting device {} configuration...".format(hostname))

                # Get a reference to the device list
                device_list = root.devices.device

                device = device_list.create(hostname)
                device.address = mgmt_ip
                device.port = 22
                device.authgroup = "dnac"
                dev_type = device.device_type.cli
                dev_type.ned_id = 'cisco-ios-cli-6.39'
                device.state.admin_state = 'unlocked'

                print('Committing the device configuration...')
                t.apply()
                print("Committed")

                # This transaction is no longer valid

            #
            # fetch-host-keys and sync-from does not require a transaction
            # continue using the Maapi object
            #
            root = ncs.maagic.get_root(m)
            device = root.devices.device[hostname]

            print("Fetching SSH keys...")
            output = device.ssh.fetch_host_keys()
            print("Result: %s" % output.result)

            print("Syncing configuration...")
            output = device.sync_from()
            print("Result: %s" % output.result)
            if not output.result:
                print("Error: %s" % output.info)