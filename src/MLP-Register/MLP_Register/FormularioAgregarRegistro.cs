using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Data.SQLite;

namespace MLP_Register
{
    public partial class FormularioAgregarRegistro : Form
    {
        private string connectionString;
        private string nombreTabla;
        
        public FormularioAgregarRegistro(string connectionString, string nombreTabla)
        {
            InitializeComponent();
            this.connectionString = connectionString;
            this.nombreTabla = nombreTabla;
        }

        private void BtnGuardar_Click_1(object sender, EventArgs e) {}
        private void BtnCancelar_Click(object sender, EventArgs e) {}

        private void btnGuardar_Click(object sender, EventArgs e)
        {
            try
            {
                // CONSTRUIR CONSULTA INSERT
                string query = $@"INSERT INTO {nombreTabla} 
                                (Matricula, Estado, [Marca/Modelo], [Color del vehiculo], [Estatus Legal], [Propietario Virtual], [Fecha de registro], Filename) 
                                VALUES (@matricula, @estado, @marca, @color, @estatusLegal, @propietario, @fecha, @filename)";

                using (SQLiteConnection conexion = new SQLiteConnection(connectionString))
                using (SQLiteCommand cmd = new SQLiteCommand(query, conexion))
                {
                    // Agregar parametros
                    cmd.Parameters.AddWithValue("@matricula", txtMatricula.Text.Trim());
                    cmd.Parameters.AddWithValue("@estado", cmbEstado.Text.Trim());
                    cmd.Parameters.AddWithValue("@marca", cmbMarca.Text.Trim());
                    cmd.Parameters.AddWithValue("@color", cmbColor.Text.Trim());
                    cmd.Parameters.AddWithValue("@estatusLegal", cmbEstatus.SelectedItem.ToString());
                    cmd.Parameters.AddWithValue("@propietario", txtPropietario.Text.Trim());
                    cmd.Parameters.AddWithValue("@fecha", dtpFechaRegistro.Value.ToString("yyyy-MM-dd"));
                    cmd.Parameters.AddWithValue("@filename", txtFilename.Text.Trim());

                    conexion.Open();
                    int filasAfectadas = cmd.ExecuteNonQuery();

                    if (filasAfectadas > 0)
                    {
                        MessageBox.Show("Registro agregado exitosamente.", "exito",
                                      MessageBoxButtons.OK, MessageBoxIcon.Information);
                        this.DialogResult = DialogResult.OK;
                        this.Close();
                    }
                    else
                    {
                        MessageBox.Show("No se pudo agregar el registro.", "Error",
                                      MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
            catch (SQLiteException ex)
            {
                if (ex.Message.Contains("UNIQUE constraint failed"))
                {
                    MessageBox.Show("Ya existe un registro con esa Matricula o Filename.\nPor favor, verifica los datos.",
                                  "Registro duplicado", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
                else
                {
                    MessageBox.Show($"Error de base de datos: {ex.Message}", "Error SQLite",
                                  MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al guardar: {ex.Message}", "Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnCancelar_Click_1(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            this.Close();
        }
    }
}
