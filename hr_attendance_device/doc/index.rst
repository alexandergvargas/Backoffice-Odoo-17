Instalación
============

1. Navegar a Aplicaciones
2. Buscar con la palabra clave 'hr_attendance_device'
3. Instálalo como de costumbre y listo.

Conceptos
========

#. **Device Location**: es un modelo para almacenar ubicaciones donde están instalados sus dispositivos de asistencia.
   Cada ubicación consta de la siguiente información.

   * Nombre: el nombre de la ubicación.
   * Zona horaria: la zona horaria de la ubicación. Esto es para admitir registros de asistencia en múltiples ubicaciones de diferentes zonas horarias.

#. **Attendance State**: es un modelo para almacenar estados de actividad de asistencia que pueden ser definidos por los usuarios.
   Los estados pueden ser Entrada, Salida, Entrada de horas extra, Inicio de horas extra, etc. Navegue hasta
   Asistencia > Configuración > Estado de asistencia para ver la lista de estados predeterminados que se crearon
   durante la instalación de esta aplicación.
#. **Attendance Activity**: is a model that classifies attendances in activities such as Normal Working, Overtime, etc.
   Navigate to Attendance > Configuration > Attendance Activity to see the list of default activities that were created during installation of this application. Each Attendance Activity is defined with the following

   * Name: the unique name of the activity
   * Attendance Status: List of the attendance states that are applied to this Activity.

#. **Device User** is a model that stores all the devices' users in your Odoo instance and map such the users with Employees
   in the system. Each Device User consists of (but not limited to) the following information

   * Name: The name of the user stored in the device
   * Attendance Device: The device to which this user belong
   * UID: The ID (technical field) of the user in the device storage, which is usually invisible at the device's inteface/screen
   * ID Number: The ID Number of the user/employee in the device storage. It is also known as "User ID" in some devices
   * Employee: the employee that is mapped with this user. If you have multiple device, each employee may map with multiple corresponding device users

#. **User Attendance**: is a model that stores all the attendance records downloaded from all the devices. In other words,
   it a central database of attendance logs for all your devices. This log will be used as the based to create HR Attendance.
   During that creation, the software will also check for a validity of the attendance to ensure that the HR Attendance data
   is clean and valid.
#. **HR Attendance**: is a model offered by the Odoo's standard module `hr_attendance` and is extended to have the following fields

   * Check In: the time of check in
   * Check Out: the time of check out
   * Employee: the related employee
   * Checkin Device: the attendance device that logged the check in
   * Checkout Device: the attendance device that logged the check out

   HR Attendance records is created automatically and periodically by the Scheduled Action named "Synchronize attendances scheduler"

#. Employee: is a model in Odoo that is extended for additional following information

   * Unmapped Devices: to show the list of attendance devices that have not get this employee mapped
   * Created from Device: to indicate if the employee profile was created from device (i.g. Download users -> auto create employee
     -> au map them). This will helps you filter your employees to see ones that were or were not created from devices

#. **Attendance Device**: is a model that store all the information of an attendance device. It also provides a lot of tools such as

   * Upload Users: to upload all your employee to an attendance device (e.g an new and fresh device)
   * Download Users: to download all the device's users data into odoo and map those users with employees (if auto mapping is set)
   * Map Employee: to map device users with employees in your Odoo instance
   * Check connection: to check if your Odoo instance could connect to the device
   * Get Device Info: to get the most important information about the device (e.g. OEM Vendor, Device Name, Serial Number,
     Firmware Version, etc)
   * Download Attendance: to download manually all the attendance data from the device into your Odoo database, although this
     could be done automatically be the scheduled action named "Download attendances scheduler"
   * Restart: to restart the device
   * Clear Data: this is to empty your data. It is very DANGEROUS function and is visible to and accessible by the HR Attendance
     Manager only
   * And many more...

Setup a new attendance device
=============================
#. Navigate to **Attendances > Attendance Devices > Devices Manager**
#. Click Create button to open device form view
#. Input the name of the device (optional)
#. Enter the IP of the device. It must be accessible from your Odoo server.
   If your Odoo instance is on the Internet while the device is in your office,
   behind a router, please insure that port forwarding is enabled and the device's network configuration is
   properly set to allow accessing your device from outside via Internet. You may need to refer to your router manufacturers for documentation on how to do NAT / port forwarding
#. Port: the port of the device. It is usually 4370
#. Protocol: which is either UDP or TCP. Most the modern devices nowadays support both. TCP is more reliable but may not be supported by a behind-a-decade device  
#. Location: the location where the device is physically installed. It is important that the time zone of the location should be correct.
#. You may want to see other options (e.g. Map Employee Before Download, Time zone, Generate Employees During Mapping, etc)
#. Hit Save button to create a new device in your Odoo.
#. Hit Check Connection to test if the connection works. If it did not work, please troubleshoot for the following cases

   * Check network setting inside the physical device: IP, Gateway, Port, Net Mask
   * Check your firewall / router to see if it blocks connection from your Odoo instance.
   * Try on switching between UDP and TCP

#. Map Devices Users and Employees

   * If this is a fresh device without any data stored inside:

     * Hit Upload users

   * If this is not a fresh device,

     * you may want to Clear Data before doing the step 10.1 mentioned above
     * Or, you may want to Download Users and map them to existing employee or create a new employee accordingly

   * Validate the result:

     * All Device Users should link to a corresponding employee
     * No unmapped employees shown on the device form view

#. Test Attendance Data download and synchronization

   * Do some check-in and check out at the physical device

     * Wait for seconds between check in and check out
     * Try some wrong actions: check in a few times before check out

   * Come back to the device form view in Odoo

     * Hit Download Attendance Data and wait for its completion. For just a few attendance records, it may take only a couple
       of seconds even your device is located in a country other than the system's

   * Validate the result

     * Navigating to **Attendances > Attendance Devices > Attendance Data** to validate if the attendance log is recorded there.
     * If found, you are done now. You can continue with the following steps to bring the new device into production

       * Clear the sample attendance data you have created:

         * Navigate to Attendances > Attendance Devices > Attendance Data, find and delete those sample records
         * Navigate to Attendances > Attendance Devices > Synchronize and hit Clear Attendance Data button
       * Hit the Confirmed state in the header of the device form view. If you don't do it, the schedulers will ignore
         the device during their runs

     * If not found, there should be some trouble that need further investigation

       * Check the connection
       * Try to get the device information
       * Check the work codes of the device if they are match with the ones specified in the "Attendance Status Codes" table
         in the device form view
       * Contact the author of the "Attendance Device" application if you could not solve the problem your self.

Set up for a new Employee
=========================
#. Create an employee as usual
#. Hit the Action button in the header area of the employee form view to find the menu item "Upload to Attendance Machine"
   in the dropped down list
#. Select the device(s) that will be used for this employee then hit Upload Employees button
#. You can also do mass upload by selecting employees from the employee list view. Or go to the devices

How the automation works
========================

There are two schedule actions:

#. **Download attendances scheduler**: By default, it runs every 30 minutes to

   * Download the attendance log/data from all your devices that are set in Confirmed status. Devices that are not in this status
     will be ignored
   * Create User Attendance records in your Odoo database
   * Depending on the configuration you made on the devices, it may also do the following automatically

     * Create new employees and map with the corresponding device users if new users are found in the devices
     * Clear the attendance data from the device if it's time to do it.

#. **Synchronize attendances scheduler**: By default, it runs every 30 minutes to

   * find the valid attendance in the user attendance log
   * create HR Attendance records from such the log
