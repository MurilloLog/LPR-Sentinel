using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.SQLite;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MLP_Register
{
    public partial class FormularioActualizarRegistro : Form
    {
        private string connectionString;
        private string nombreTabla;
        private string matriculaOriginal;
        public FormularioActualizarRegistro(string connectionString, string nombreTabla, DataGridViewRow filaSeleccionada)
        {
            InitializeComponent();
            this.connectionString = connectionString;
            this.nombreTabla = nombreTabla;

            // Cargar los datos actuales en el formulario
            CargarDatosActuales(filaSeleccionada);
        }

        private void CargarDatosActuales(DataGridViewRow fila)
        {
            // Guardar la matricula original para usarla en el UPDATE
            matriculaOriginal = fila.Cells["Matricula"].Value.ToString();

            // Crear variables temporales con los valores actuales
            txtMatriculaActual.Text = fila.Cells["Matricula"].Value?.ToString() ?? "";
            txtEstadoActual.Text = fila.Cells["Estado"].Value?.ToString() ?? "";
            txtMarcaActual.Text = fila.Cells["Marca/Modelo"].Value?.ToString() ?? "";
            txtColorActual.Text = fila.Cells["Color del vehiculo"].Value?.ToString() ?? "";
            txtEstatusActual.Text = fila.Cells["Estatus Legal"].Value?.ToString() ?? "";
            txtPropietarioActual.Text = fila.Cells["Propietario Virtual"].Value?.ToString() ?? "";
            txtFilenameActual.Text = fila.Cells["Filename"].Value?.ToString() ?? "";
            txtFechaActual.Text = fila.Cells["Fecha de registro"].Value?.ToString() ?? "";
        }

        private void lblTitle_Click(object sender, EventArgs e)
        {

        }

        private void btnGuardar_Click(object sender, EventArgs e)
        {
            try
            {
                // VALIDACIONES
                if (string.IsNullOrWhiteSpace(txtMatricula.Text))
                {
                    MessageBox.Show("La Matricula es obligatoria.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    txtMatricula.Focus();
                    return;
                }

                if (string.IsNullOrWhiteSpace(cmbEstado.Text))
                {
                    MessageBox.Show("El Estado es obligatorio.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    cmbEstado.Focus();
                    return;
                }

                if (string.IsNullOrWhiteSpace(cmbMarca.Text))
                {
                    MessageBox.Show("La Marca/Modelo es obligatorio.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    cmbMarca.Focus();
                    return;
                }

                if (string.IsNullOrWhiteSpace(cmbColor.Text))
                {
                    MessageBox.Show("El Color del vehiculo es obligatorio.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    cmbColor.Focus();
                    return;
                }

                if (cmbEstatus.SelectedItem == null)
                {
                    MessageBox.Show("Debes seleccionar un Estatus Legal.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    cmbEstatus.Focus();
                    return;
                }

                if (string.IsNullOrWhiteSpace(txtPropietario.Text))
                {
                    MessageBox.Show("El Propietario Virtual es obligatorio.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    txtPropietario.Focus();
                    return;
                }

                if (string.IsNullOrWhiteSpace(txtFilename.Text))
                {
                    MessageBox.Show("El Filename es obligatorio.", "Campo requerido",
                                  MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    txtFilename.Focus();
                    return;
                }

                // CONSTRUIR CONSULTA UPDATE
                string query = $@"UPDATE [{nombreTabla}] SET 
                                Matricula = @matricula,
                                Estado = @estado,
                                [Marca/Modelo] = @marca,
                                [Color del vehiculo] = @color,
                                [Estatus Legal] = @estatusLegal,
                                [Propietario Virtual] = @propietario,
                                [Fecha de registro] = @fecha,
                                Filename = @filename
                                WHERE Matricula = @matriculaOriginal";

                using (SQLiteConnection conexion = new SQLiteConnection(connectionString))
                using (SQLiteCommand cmd = new SQLiteCommand(query, conexion))
                {
                    // Agregar parametros con los nuevos valores
                    cmd.Parameters.AddWithValue("@matricula", txtMatricula.Text.Trim());
                    cmd.Parameters.AddWithValue("@estado", cmbEstado.Text.Trim());
                    cmd.Parameters.AddWithValue("@marca", cmbMarca.Text.Trim());
                    cmd.Parameters.AddWithValue("@color", cmbColor.Text.Trim());
                    cmd.Parameters.AddWithValue("@estatusLegal", cmbEstatus.SelectedItem.ToString());
                    cmd.Parameters.AddWithValue("@propietario", txtPropietario.Text.Trim());
                    cmd.Parameters.AddWithValue("@fecha", dtpFechaRegistro.Value.ToString("yyyy-MM-dd"));
                    cmd.Parameters.AddWithValue("@filename", txtFilename.Text.Trim());
                    cmd.Parameters.AddWithValue("@matriculaOriginal", matriculaOriginal);

                    conexion.Open();
                    int filasAfectadas = cmd.ExecuteNonQuery();

                    if (filasAfectadas > 0)
                    {
                        MessageBox.Show("Registro actualizado exitosamente.", "exito",
                                      MessageBoxButtons.OK, MessageBoxIcon.Information);
                        this.DialogResult = DialogResult.OK;
                        this.Close();
                    }
                    else
                    {
                        MessageBox.Show("No se pudo actualizar el registro. Es posible que haya sido eliminado.",
                                      "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
                MessageBox.Show($"Error al actualizar: {ex.Message}", "Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnCancelar_Click(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            this.Close();
        }
    }
}
