using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.SQLite;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MLP_Register
{
    public partial class Form1 : Form
    {
        // Variable para almacenar la ruta del archivo DB seleccionado
        private string rutaArchivoDB = string.Empty;

        // Variable para la cadena de conexion
        private string connectionString = string.Empty;

        // Obtener el nombre de la tabla actual desde el DataGridView o almacenarlo al cargar
        string nombreTabla = "Registros";

        // Variable para almacenar la clave del registro seleccionado
        private string matriculaSeleccionada = string.Empty;

        public Form1()
        {
            InitializeComponent();
        }

        private void CargarBaseDeDatos(string rutaArchivo)
        {
            try
            {
                // Validar que el archivo existe
                if (!File.Exists(rutaArchivo))
                {
                    MessageBox.Show("El archivo no existe.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                // Construir la cadena de conexion dinamica
                connectionString = $"Data Source={rutaArchivo};Version=3;";

                using (SQLiteConnection conexion = new SQLiteConnection(connectionString))
                {
                    conexion.Open();

                    // Obtener el nombre de la primera tabla (o puedes permitir que el usuario elija)
                    string obtenerTablas = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'";
                    using (SQLiteCommand cmd = new SQLiteCommand(obtenerTablas, conexion))
                    {
                        using (SQLiteDataReader reader = cmd.ExecuteReader())
                        {
                            if (reader.Read())
                            {
                                string nombreTabla = reader["name"].ToString();

                                // Cargar los datos de esa tabla
                                string query = $"SELECT * FROM [{nombreTabla}]";
                                SQLiteDataAdapter adapter = new SQLiteDataAdapter(query, conexion);
                                DataTable dataTable = new DataTable();
                                adapter.Fill(dataTable);

                                // Mostrar en el DataGridView
                                dataGridView1.DataSource = dataTable;

                                // Opcional: Ajustar el ancho de las columnas automaticamente
                                dataGridView1.AutoResizeColumns(DataGridViewAutoSizeColumnsMode.AllCells);

                                // Actualizar el texto del formulario para mostrar que archivo esta cargado
                                this.Text = $"MLP-Register: {Path.GetFileName(rutaArchivo)}";

                                MessageBox.Show($"Base de datos cargada exitosamente.\nTabla: {nombreTabla}\nRegistros: {dataTable.Rows.Count}",
                                                "exito", MessageBoxButtons.OK, MessageBoxIcon.Information);
                            }
                            else
                            {
                                MessageBox.Show("No se encontraron tablas en la base de datos.", "Advertencia", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                                dataGridView1.DataSource = null;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al cargar la base de datos:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                dataGridView1.DataSource = null;
            }
        }

        private void LimpiarDataGridView()
        {
            dataGridView1.DataSource = null;
            rutaArchivoDB = string.Empty;
            connectionString = string.Empty;
            this.Text = "MLP-Register: Sin archivo cargado";

            // Opcional: Limpiar tambien los TextBox de entrada
            //txtNombre.Text = string.Empty;
            //txtTelefono.Text = string.Empty;
            //txtEmail.Text = string.Empty;
        }

        private void btnLoadDB_Click(object sender, EventArgs e)
        {
            // Configurar y mostrar el dialogo de seleccion de archivo
            openFileDialog1.Filter = "Archivos SQLite (*.db;*.sqlite;*.sqlite3)|*.db;*.sqlite;*.sqlite3|Todos los archivos (*.*)|*.*";
            openFileDialog1.Title = "Selecciona tu archivo de base de datos";
            openFileDialog1.InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);

            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                // Guardar la ruta seleccionada
                rutaArchivoDB = openFileDialog1.FileName;

                // Cargar la base de datos
                CargarBaseDeDatos(rutaArchivoDB);
            }
        }

        private void btnClearData_Click(object sender, EventArgs e)
        {
            LimpiarDataGridView();
        }

        private void btnAddRegister_Click(object sender, EventArgs e)
        {
            // Verificar que hay una base de datos cargada
            if (string.IsNullOrEmpty(connectionString) || string.IsNullOrEmpty(rutaArchivoDB))
            {
                MessageBox.Show("Primero debes cargar una base de datos usando el boton 'Cargar Datos'.",
                              "Sin conexion", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Verificar que el DataGridView tiene datos cargados
            if (dataGridView1.DataSource == null || dataGridView1.Rows.Count == 0)
            {
                MessageBox.Show("No hay ninguna tabla cargada. Por favor, carga una base de datos primero.",
                              "Sin datos", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            


            // Crear y mostrar el formulario de agregar
            using (FormularioAgregarRegistro formAgregar = new FormularioAgregarRegistro(connectionString, nombreTabla))
            {
                if (formAgregar.ShowDialog() == DialogResult.OK)
                {
                    // Recargar los datos en el DataGridView despues de agregar
                    CargarBaseDeDatos(rutaArchivoDB);

                    // Mostrar un mensaje de confirmacion
                    MessageBox.Show("Los datos se han actualizado correctamente.",
                                  "Actualizacion completada", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
        }

        private void dataGridView1_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {
            // Verificar que se hizo clic en una fila valida (no en el encabezado)
            if (e.RowIndex >= 0)
            {
                // Obtener la fila seleccionada
                DataGridViewRow row = dataGridView1.Rows[e.RowIndex];

                if (row.Cells["Matricula"].Value != null)
                {
                    matriculaSeleccionada = row.Cells["Matricula"].Value.ToString();

                    // Mostrar la matricula seleccionada en el titulo del formulario
                    this.Text = $"MLP-Register: Registro seleccionado: {matriculaSeleccionada}";
                }
            }
        }

        private void btnDeleteRegister_Click(object sender, EventArgs e)
        {
            // Verificar que hay una base de datos cargada
            if (string.IsNullOrEmpty(connectionString) || string.IsNullOrEmpty(rutaArchivoDB))
            {
                MessageBox.Show("Primero debes cargar una base de datos.",
                              "Sin conexion", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Verificar que hay un registro seleccionado
            if (string.IsNullOrEmpty(matriculaSeleccionada))
            {
                MessageBox.Show("Por favor, selecciona un registro haciendo clic en una fila del listado.",
                              "Ningun registro seleccionado", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Confirmar eliminacion con el usuario
            DialogResult confirmacion = MessageBox.Show(
                $"¿Estas seguro de que deseas eliminar el registro con matricula '{matriculaSeleccionada}'?\n\nEsta accion no se puede deshacer.",
                "Confirmar eliminacion",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning);

            if (confirmacion == DialogResult.Yes)
            {
                try
                {
                    // Construir consulta DELETE usando la matricula como identificador
                    string query = $"DELETE FROM [{nombreTabla}] WHERE Matricula = @matricula";

                    using (SQLiteConnection conexion = new SQLiteConnection(connectionString))
                    using (SQLiteCommand cmd = new SQLiteCommand(query, conexion))
                    {
                        cmd.Parameters.AddWithValue("@matricula", matriculaSeleccionada);

                        conexion.Open();
                        int filasAfectadas = cmd.ExecuteNonQuery();

                        if (filasAfectadas > 0)
                        {
                            MessageBox.Show($"Registro con matricula '{matriculaSeleccionada}' eliminado exitosamente.",
                                          "Eliminacion completada", MessageBoxButtons.OK, MessageBoxIcon.Information);

                            // Limpiar la seleccion
                            matriculaSeleccionada = string.Empty;
                            this.Text = "MLP-Register: Sin registro seleccionado";

                            // Recargar los datos en el DataGridView
                            CargarBaseDeDatos(rutaArchivoDB);
                        }
                        else
                        {
                            MessageBox.Show("No se encontro el registro para eliminar. Es posible que ya haya sido eliminado.",
                                          "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        }
                    }
                }
                catch (SQLiteException ex)
                {
                    MessageBox.Show($"Error de base de datos al eliminar:\n{ex.Message}",
                                  "Error SQLite", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error inesperado:\n{ex.Message}",
                                  "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void btnUpdateRegister_Click(object sender, EventArgs e)
        {
            // Verificar que hay una base de datos cargada
            if (string.IsNullOrEmpty(connectionString) || string.IsNullOrEmpty(rutaArchivoDB))
            {
                MessageBox.Show("Primero debes cargar una base de datos usando el boton 'Cargar Datos'.",
                              "Sin conexion", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Verificar que hay un registro seleccionado
            if (dataGridView1.SelectedRows.Count == 0)
            {
                MessageBox.Show("Por favor, selecciona un registro haciendo clic en una fila del listado.",
                              "Ningun registro seleccionado", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Obtener la fila seleccionada
            DataGridViewRow filaSeleccionada = dataGridView1.SelectedRows[0];

            // Verificar que la fila tiene datos
            if (filaSeleccionada.Cells["Matricula"].Value == null)
            {
                MessageBox.Show("El registro seleccionado no tiene una matricula valida.",
                              "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            // Crear y mostrar el formulario de actualizacion
            using (FormularioActualizarRegistro formActualizar = new FormularioActualizarRegistro(
                connectionString,
                nombreTabla,
                filaSeleccionada))
            {
                if (formActualizar.ShowDialog() == DialogResult.OK)
                {
                    // Recargar los datos en el DataGridView despues de actualizar
                    CargarBaseDeDatos(rutaArchivoDB);

                    // Opcional: Mostrar mensaje de confirmacion
                    MessageBox.Show("Los datos se han actualizado correctamente.",
                                  "Actualizacion completada", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
        }

        private void btnBuscarRegistro_Click(object sender, EventArgs e)
        {
            // Verificar que hay una base de datos cargada
            if (string.IsNullOrEmpty(connectionString) || string.IsNullOrEmpty(rutaArchivoDB))
            {
                MessageBox.Show("Primero debes cargar una base de datos usando el boton 'Cargar Datos'.",
                              "Sin conexion", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Verificar que hay una tabla cargada
            if (string.IsNullOrEmpty(nombreTabla))
            {
                MessageBox.Show("No hay ninguna tabla cargada. Por favor, carga una base de datos primero.",
                              "Sin datos", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Crear y mostrar el formulario de busqueda
            using (FormularioBusqueda formBusqueda = new FormularioBusqueda(connectionString, nombreTabla))
            {
                formBusqueda.ShowDialog();
            }
        }

        private void lblLinkGitHub_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            // Marca el enlace como visitado (cambia el color)
            lblLinkGitHub.LinkVisited = true;

            // Abre el enlace en el navegador predeterminado
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = "https://github.com/MurilloLog",
                UseShellExecute = true
            });
        }
    }
}