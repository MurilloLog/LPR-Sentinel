using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.SQLite;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MLP_Register
{
    public partial class FormularioBusqueda : Form
    {
        private string connectionString;
        private string nombreTabla;

        private void LimpiarResultados()
        {
            txtMatriculaBuscar.Text = "";
            txtMatriculaActual.Text = "";
            txtTimestamp.Text = "";
            txtEstadoActual.Text = "";
            txtMarcaActual.Text = "";
            txtColorActual.Text = "";
            txtEstatusActual.Text = "";
            txtPropietarioActual.Text = "";
            txtFechaActual.Text = "";
            txtFilenameActual.Text = "";

            txtMatriculaBuscar.BackColor = System.Drawing.Color.White;
            txtMatriculaActual.BackColor = System.Drawing.Color.Gainsboro;
            txtTimestamp.BackColor = System.Drawing.Color.Gainsboro;
            txtEstadoActual.BackColor = System.Drawing.Color.Gainsboro;
            txtMarcaActual.BackColor = System.Drawing.Color.Gainsboro;
            txtColorActual.BackColor = System.Drawing.Color.Gainsboro;
            txtEstatusActual.BackColor = System.Drawing.Color.Gainsboro;
            txtPropietarioActual.BackColor = System.Drawing.Color.Gainsboro;
            txtFechaActual.BackColor = System.Drawing.Color.Gainsboro;
            txtFilenameActual.BackColor = System.Drawing.Color.Gainsboro;
        }

        public FormularioBusqueda(string connectionString, string nombreTabla)
        {
            InitializeComponent();
            this.connectionString = connectionString;
            this.nombreTabla = nombreTabla;

            txtMatriculaBuscar.BackColor = System.Drawing.Color.White;
            txtMatriculaActual.BackColor = System.Drawing.Color.Gainsboro;
            txtTimestamp.BackColor = System.Drawing.Color.Gainsboro;
            txtEstadoActual.BackColor = System.Drawing.Color.Gainsboro;
            txtMarcaActual.BackColor = System.Drawing.Color.Gainsboro;
            txtColorActual.BackColor = System.Drawing.Color.Gainsboro;
            txtEstatusActual.BackColor = System.Drawing.Color.Gainsboro;
            txtPropietarioActual.BackColor = System.Drawing.Color.Gainsboro;
            txtFechaActual.BackColor = System.Drawing.Color.Gainsboro;
            txtFilenameActual.BackColor = System.Drawing.Color.Gainsboro;
        }

        private void lblInstruction_Click(object sender, EventArgs e)
        {

        }

        private void btnBuscar_Click(object sender, EventArgs e)
        {
            string matricula = txtMatriculaBuscar.Text.Trim().ToUpper();

            if (string.IsNullOrEmpty(matricula))
            {
                MessageBox.Show("Por favor, ingrese una matricula para buscar.",
                              "Entrada requerida", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                txtMatriculaBuscar.Focus();
                return;
            }

            // Limpiar resultados anteriores antes de la nueva busqueda
            LimpiarResultados();

            // Iniciar temporizador
            Stopwatch stopwatch = new Stopwatch();
            stopwatch.Start();

            try
            {
                using (SQLiteConnection conexion = new SQLiteConnection(connectionString))
                {
                    conexion.Open();

                    // Construir consulta de busqueda
                    string query = $@"SELECT * FROM [{nombreTabla}] 
                                    WHERE Matricula = @matricula";

                    using (SQLiteCommand cmd = new SQLiteCommand(query, conexion))
                    {
                        cmd.Parameters.AddWithValue("@matricula", matricula);

                        using (SQLiteDataReader reader = cmd.ExecuteReader())
                        {
                            // Detener temporizador despues de ejecutar la consulta
                            stopwatch.Stop();
                            txtTimestamp.Text = stopwatch.ElapsedMilliseconds.ToString();

                            if (reader.Read())
                            {
                                txtMatriculaActual.Text = reader["Matricula"]?.ToString() ?? "";
                                txtEstadoActual.Text = reader["Estado"]?.ToString() ?? "";
                                txtMarcaActual.Text = reader["Marca/Modelo"]?.ToString() ?? "";
                                txtColorActual.Text = reader["Color del vehiculo"]?.ToString() ?? "";
                                txtEstatusActual.Text = reader["Estatus Legal"]?.ToString() ?? "";
                                txtPropietarioActual.Text = reader["Propietario Virtual"]?.ToString() ?? "";
                                txtFechaActual.Text = reader["Fecha de registro"]?.ToString() ?? "";
                                txtFilenameActual.Text = reader["Filename"]?.ToString() ?? "";

                                // Cambiar color de fondo para indicar exito
                                txtMatriculaActual.BackColor = System.Drawing.Color.Honeydew;
                                txtTimestamp.BackColor = System.Drawing.Color.Honeydew;
                                txtEstadoActual.BackColor = System.Drawing.Color.Honeydew;
                                txtMarcaActual.BackColor = System.Drawing.Color.Honeydew;
                                txtColorActual.BackColor = System.Drawing.Color.Honeydew;
                                txtEstatusActual.BackColor = System.Drawing.Color.Honeydew;
                                txtPropietarioActual.BackColor = System.Drawing.Color.Honeydew;
                                txtFechaActual.BackColor = System.Drawing.Color.Honeydew;
                                txtFilenameActual.BackColor = System.Drawing.Color.Honeydew;
                            }
                            else
                            {
                                // No se encontro el registro
                                MessageBox.Show($"No se encontro ningun registro con la matricula '{matricula}'.",
                                              "Sin resultados", MessageBoxButtons.OK, MessageBoxIcon.Information);
                                this.Text = "Busqueda por Matricula - Sin resultados";

                                // Mantener los TextBox en color gris indicando "sin datos"
                                txtMatriculaBuscar.BackColor = System.Drawing.Color.White;
                                txtMatriculaActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtTimestamp.BackColor = System.Drawing.Color.Gainsboro;
                                txtEstadoActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtMarcaActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtColorActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtEstatusActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtPropietarioActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtFechaActual.BackColor = System.Drawing.Color.Gainsboro;
                                txtFilenameActual.BackColor = System.Drawing.Color.Gainsboro;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                txtTimestamp.Text = stopwatch.ElapsedMilliseconds.ToString();

                MessageBox.Show($"Error al realizar la busqueda:\n{ex.Message}",
                              "Error de busqueda", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnLimpiar_Click(object sender, EventArgs e)
        {
            LimpiarResultados();
        }

        private void label1_Click(object sender, EventArgs e)
        {

        }
    }
}
