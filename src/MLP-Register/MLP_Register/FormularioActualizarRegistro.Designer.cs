namespace MLP_Register
{
    partial class FormularioActualizarRegistro
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(FormularioActualizarRegistro));
            this.btnCancelar = new System.Windows.Forms.Button();
            this.btnGuardar = new System.Windows.Forms.Button();
            this.txtFilename = new System.Windows.Forms.TextBox();
            this.dtpFechaRegistro = new System.Windows.Forms.DateTimePicker();
            this.txtPropietario = new System.Windows.Forms.TextBox();
            this.cmbEstatus = new System.Windows.Forms.ComboBox();
            this.cmbColor = new System.Windows.Forms.ComboBox();
            this.cmbMarca = new System.Windows.Forms.ComboBox();
            this.cmbEstado = new System.Windows.Forms.ComboBox();
            this.txtMatricula = new System.Windows.Forms.TextBox();
            this.label9 = new System.Windows.Forms.Label();
            this.label8 = new System.Windows.Forms.Label();
            this.label7 = new System.Windows.Forms.Label();
            this.label6 = new System.Windows.Forms.Label();
            this.label5 = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.label1 = new System.Windows.Forms.Label();
            this.txtMatriculaActual = new System.Windows.Forms.TextBox();
            this.txtFilenameActual = new System.Windows.Forms.TextBox();
            this.label10 = new System.Windows.Forms.Label();
            this.txtPropietarioActual = new System.Windows.Forms.TextBox();
            this.txtEstadoActual = new System.Windows.Forms.TextBox();
            this.txtMarcaActual = new System.Windows.Forms.TextBox();
            this.txtColorActual = new System.Windows.Forms.TextBox();
            this.txtEstatusActual = new System.Windows.Forms.TextBox();
            this.txtFechaActual = new System.Windows.Forms.TextBox();
            this.pictureBox1 = new System.Windows.Forms.PictureBox();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).BeginInit();
            this.SuspendLayout();
            // 
            // btnCancelar
            // 
            this.btnCancelar.BackColor = System.Drawing.Color.LightGray;
            this.btnCancelar.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnCancelar.Location = new System.Drawing.Point(576, 332);
            this.btnCancelar.Name = "btnCancelar";
            this.btnCancelar.Size = new System.Drawing.Size(99, 40);
            this.btnCancelar.TabIndex = 37;
            this.btnCancelar.Text = "Cancelar";
            this.btnCancelar.UseVisualStyleBackColor = false;
            this.btnCancelar.Click += new System.EventHandler(this.btnCancelar_Click);
            // 
            // btnGuardar
            // 
            this.btnGuardar.BackColor = System.Drawing.Color.PaleGreen;
            this.btnGuardar.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnGuardar.Location = new System.Drawing.Point(436, 332);
            this.btnGuardar.Name = "btnGuardar";
            this.btnGuardar.Size = new System.Drawing.Size(99, 40);
            this.btnGuardar.TabIndex = 36;
            this.btnGuardar.Text = "Actualizar";
            this.btnGuardar.UseVisualStyleBackColor = false;
            this.btnGuardar.Click += new System.EventHandler(this.btnGuardar_Click);
            // 
            // txtFilename
            // 
            this.txtFilename.Location = new System.Drawing.Point(436, 296);
            this.txtFilename.Name = "txtFilename";
            this.txtFilename.Size = new System.Drawing.Size(239, 20);
            this.txtFilename.TabIndex = 35;
            // 
            // dtpFechaRegistro
            // 
            this.dtpFechaRegistro.Location = new System.Drawing.Point(436, 262);
            this.dtpFechaRegistro.Name = "dtpFechaRegistro";
            this.dtpFechaRegistro.Size = new System.Drawing.Size(239, 20);
            this.dtpFechaRegistro.TabIndex = 34;
            // 
            // txtPropietario
            // 
            this.txtPropietario.Location = new System.Drawing.Point(436, 222);
            this.txtPropietario.Name = "txtPropietario";
            this.txtPropietario.Size = new System.Drawing.Size(239, 20);
            this.txtPropietario.TabIndex = 33;
            // 
            // cmbEstatus
            // 
            this.cmbEstatus.FormattingEnabled = true;
            this.cmbEstatus.Items.AddRange(new object[] {
            "Activo",
            "Robado",
            "Recuperado",
            "En Proceso Legal",
            "Baja Temporal",
            "Baja Definitiva",
            "Reposicion",
            "Homologacion",
            "Importacion Temporal",
            "Importacion Definitiva",
            "Remarcaje",
            "Irregular",
            "Cancelado"});
            this.cmbEstatus.Location = new System.Drawing.Point(436, 188);
            this.cmbEstatus.Name = "cmbEstatus";
            this.cmbEstatus.Size = new System.Drawing.Size(239, 21);
            this.cmbEstatus.TabIndex = 32;
            // 
            // cmbColor
            // 
            this.cmbColor.FormattingEnabled = true;
            this.cmbColor.Items.AddRange(new object[] {
            "Blanco",
            "Negro",
            "Gris",
            "Plateado",
            "Azul",
            "Rojo",
            "Verde",
            "Vino",
            "Cafe",
            "Beige",
            "Dorado",
            "Naranja",
            "Amarillo",
            "Morado",
            "Gris Oscuro",
            "Azul Marino",
            "Rojo Oscuro",
            "Verde Oscuro",
            "Blanco Perlado",
            "Otro"});
            this.cmbColor.Location = new System.Drawing.Point(436, 151);
            this.cmbColor.Name = "cmbColor";
            this.cmbColor.Size = new System.Drawing.Size(239, 21);
            this.cmbColor.TabIndex = 31;
            // 
            // cmbMarca
            // 
            this.cmbMarca.FormattingEnabled = true;
            this.cmbMarca.Items.AddRange(new object[] {
            "Nissan Versa",
            "Nissan Sentra",
            "Nissan NP300",
            "Nissan March",
            "Chevrolet Aveo",
            "Chevrolet Spark",
            "Chevrolet Beat",
            "Chevrolet Cruze",
            "Volkswagen Vento",
            "Volkswagen Jetta",
            "Volkswagen Golf",
            "Volkswagen Amarok",
            "Toyota Corolla",
            "Toyota Hilux",
            "Toyota Yaris",
            "Toyota Prius",
            "Honda Civic",
            "Honda CR-V",
            "Honda Accord",
            "Honda HR-V",
            "Mazda 3",
            "Mazda CX-5",
            "Mazda 2",
            "Mazda MX-5",
            "Ford Fiesta",
            "Ford Focus",
            "Ford Fusion",
            "Ford Ranger",
            "Kia Rio",
            "Kia Forte",
            "Kia Sportage",
            "Kia Sorento",
            "Hyundai Accent",
            "Hyundai Elantra",
            "Hyundai Tucson",
            "Hyundai Santa Fe",
            "Fiat 500",
            "Fiat Argo",
            "Fiat Cronos",
            "Fiat Toro",
            "Renault Kwid",
            "Renault Duster",
            "Renault Logan",
            "Renault Sandero",
            "Peugeot 208",
            "Peugeot 308",
            "Peugeot 3008",
            "Peugeot 5008",
            "BMW 3 Series",
            "BMW X5",
            "BMW X3",
            "BMW 5 Series",
            "Mercedes-Benz A-Class",
            "Mercedes-Benz C-Class",
            "Mercedes-Benz GLA",
            "Mercedes-Benz GLC",
            "Audi A3",
            "Audi A4",
            "Audi Q3",
            "Audi Q5",
            "Jeep Wrangler",
            "Jeep Grand Cherokee",
            "Jeep Compass",
            "Jeep Renegade",
            "Otro"});
            this.cmbMarca.Location = new System.Drawing.Point(436, 114);
            this.cmbMarca.Name = "cmbMarca";
            this.cmbMarca.Size = new System.Drawing.Size(239, 21);
            this.cmbMarca.TabIndex = 30;
            // 
            // cmbEstado
            // 
            this.cmbEstado.FormattingEnabled = true;
            this.cmbEstado.Items.AddRange(new object[] {
            "ags",
            "bc",
            "bcs",
            "camp",
            "chis",
            "chih",
            "coah",
            "col",
            "df",
            "dgo",
            "gto",
            "gro",
            "hgo",
            "jal",
            "mex",
            "mich",
            "mor",
            "nay",
            "nl",
            "oax",
            "pue",
            "qro",
            "qr",
            "slp",
            "sin",
            "son",
            "tab",
            "tamps",
            "tlax",
            "ver",
            "yuc",
            "zac"});
            this.cmbEstado.Location = new System.Drawing.Point(436, 77);
            this.cmbEstado.Name = "cmbEstado";
            this.cmbEstado.Size = new System.Drawing.Size(239, 21);
            this.cmbEstado.TabIndex = 29;
            // 
            // txtMatricula
            // 
            this.txtMatricula.Location = new System.Drawing.Point(436, 40);
            this.txtMatricula.Name = "txtMatricula";
            this.txtMatricula.Size = new System.Drawing.Size(239, 20);
            this.txtMatricula.TabIndex = 28;
            // 
            // label9
            // 
            this.label9.AutoSize = true;
            this.label9.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label9.Location = new System.Drawing.Point(10, 299);
            this.label9.Name = "label9";
            this.label9.Size = new System.Drawing.Size(131, 17);
            this.label9.TabIndex = 27;
            this.label9.Text = "Nombre del archivo";
            // 
            // label8
            // 
            this.label8.AutoSize = true;
            this.label8.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label8.Location = new System.Drawing.Point(10, 262);
            this.label8.Name = "label8";
            this.label8.Size = new System.Drawing.Size(119, 17);
            this.label8.TabIndex = 26;
            this.label8.Text = "Fecha de registro";
            // 
            // label7
            // 
            this.label7.AutoSize = true;
            this.label7.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label7.Location = new System.Drawing.Point(10, 225);
            this.label7.Name = "label7";
            this.label7.Size = new System.Drawing.Size(77, 17);
            this.label7.TabIndex = 25;
            this.label7.Text = "Propietario";
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label6.Location = new System.Drawing.Point(10, 188);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(89, 17);
            this.label6.TabIndex = 24;
            this.label6.Text = "Estatus legal";
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label5.Location = new System.Drawing.Point(10, 151);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(120, 17);
            this.label5.TabIndex = 23;
            this.label5.Text = "Color del vehiculo";
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label4.Location = new System.Drawing.Point(10, 114);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(126, 17);
            this.label4.TabIndex = 22;
            this.label4.Text = "Marca del vehiculo";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label3.Location = new System.Drawing.Point(10, 77);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(124, 17);
            this.label3.TabIndex = 21;
            this.label3.Text = "Estado de registro";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label2.Location = new System.Drawing.Point(10, 40);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(65, 17);
            this.label2.TabIndex = 20;
            this.label2.Text = "Matricula";
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label1.Location = new System.Drawing.Point(501, 11);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(112, 17);
            this.label1.TabIndex = 38;
            this.label1.Text = "Nuevos datos:";
            // 
            // txtMatriculaActual
            // 
            this.txtMatriculaActual.Enabled = false;
            this.txtMatriculaActual.Location = new System.Drawing.Point(146, 40);
            this.txtMatriculaActual.Name = "txtMatriculaActual";
            this.txtMatriculaActual.Size = new System.Drawing.Size(239, 20);
            this.txtMatriculaActual.TabIndex = 28;
            this.txtMatriculaActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // txtFilenameActual
            // 
            this.txtFilenameActual.Enabled = false;
            this.txtFilenameActual.Location = new System.Drawing.Point(146, 296);
            this.txtFilenameActual.Name = "txtFilenameActual";
            this.txtFilenameActual.Size = new System.Drawing.Size(239, 20);
            this.txtFilenameActual.TabIndex = 35;
            this.txtFilenameActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // label10
            // 
            this.label10.AutoSize = true;
            this.label10.Font = new System.Drawing.Font("Microsoft Sans Serif", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label10.Location = new System.Drawing.Point(192, 11);
            this.label10.Name = "label10";
            this.label10.Size = new System.Drawing.Size(121, 17);
            this.label10.TabIndex = 38;
            this.label10.Text = "Datos actuales:";
            // 
            // txtPropietarioActual
            // 
            this.txtPropietarioActual.Enabled = false;
            this.txtPropietarioActual.Location = new System.Drawing.Point(146, 222);
            this.txtPropietarioActual.Name = "txtPropietarioActual";
            this.txtPropietarioActual.Size = new System.Drawing.Size(239, 20);
            this.txtPropietarioActual.TabIndex = 33;
            this.txtPropietarioActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // txtEstadoActual
            // 
            this.txtEstadoActual.Enabled = false;
            this.txtEstadoActual.Location = new System.Drawing.Point(146, 78);
            this.txtEstadoActual.Name = "txtEstadoActual";
            this.txtEstadoActual.Size = new System.Drawing.Size(239, 20);
            this.txtEstadoActual.TabIndex = 39;
            this.txtEstadoActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // txtMarcaActual
            // 
            this.txtMarcaActual.Enabled = false;
            this.txtMarcaActual.Location = new System.Drawing.Point(146, 115);
            this.txtMarcaActual.Name = "txtMarcaActual";
            this.txtMarcaActual.Size = new System.Drawing.Size(239, 20);
            this.txtMarcaActual.TabIndex = 40;
            this.txtMarcaActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // txtColorActual
            // 
            this.txtColorActual.Enabled = false;
            this.txtColorActual.Location = new System.Drawing.Point(146, 152);
            this.txtColorActual.Name = "txtColorActual";
            this.txtColorActual.Size = new System.Drawing.Size(239, 20);
            this.txtColorActual.TabIndex = 41;
            this.txtColorActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // txtEstatusActual
            // 
            this.txtEstatusActual.Enabled = false;
            this.txtEstatusActual.Location = new System.Drawing.Point(146, 189);
            this.txtEstatusActual.Name = "txtEstatusActual";
            this.txtEstatusActual.Size = new System.Drawing.Size(239, 20);
            this.txtEstatusActual.TabIndex = 42;
            this.txtEstatusActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // txtFechaActual
            // 
            this.txtFechaActual.Enabled = false;
            this.txtFechaActual.Location = new System.Drawing.Point(146, 262);
            this.txtFechaActual.Name = "txtFechaActual";
            this.txtFechaActual.Size = new System.Drawing.Size(239, 20);
            this.txtFechaActual.TabIndex = 43;
            this.txtFechaActual.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // pictureBox1
            // 
            this.pictureBox1.Image = ((System.Drawing.Image)(resources.GetObject("pictureBox1.Image")));
            this.pictureBox1.InitialImage = ((System.Drawing.Image)(resources.GetObject("pictureBox1.InitialImage")));
            this.pictureBox1.Location = new System.Drawing.Point(391, 141);
            this.pictureBox1.Name = "pictureBox1";
            this.pictureBox1.Size = new System.Drawing.Size(40, 40);
            this.pictureBox1.SizeMode = System.Windows.Forms.PictureBoxSizeMode.StretchImage;
            this.pictureBox1.TabIndex = 44;
            this.pictureBox1.TabStop = false;
            // 
            // FormularioActualizarRegistro
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(709, 382);
            this.Controls.Add(this.pictureBox1);
            this.Controls.Add(this.txtFechaActual);
            this.Controls.Add(this.txtEstatusActual);
            this.Controls.Add(this.txtColorActual);
            this.Controls.Add(this.txtMarcaActual);
            this.Controls.Add(this.txtEstadoActual);
            this.Controls.Add(this.label10);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.btnCancelar);
            this.Controls.Add(this.btnGuardar);
            this.Controls.Add(this.txtFilenameActual);
            this.Controls.Add(this.txtFilename);
            this.Controls.Add(this.dtpFechaRegistro);
            this.Controls.Add(this.txtPropietarioActual);
            this.Controls.Add(this.txtPropietario);
            this.Controls.Add(this.cmbEstatus);
            this.Controls.Add(this.cmbColor);
            this.Controls.Add(this.cmbMarca);
            this.Controls.Add(this.cmbEstado);
            this.Controls.Add(this.txtMatriculaActual);
            this.Controls.Add(this.txtMatricula);
            this.Controls.Add(this.label9);
            this.Controls.Add(this.label8);
            this.Controls.Add(this.label7);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.label5);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.label2);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
            this.MaximizeBox = false;
            this.Name = "FormularioActualizarRegistro";
            this.ShowIcon = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent;
            this.Text = "Actualizacion de registro";
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button btnCancelar;
        private System.Windows.Forms.Button btnGuardar;
        private System.Windows.Forms.TextBox txtFilename;
        private System.Windows.Forms.DateTimePicker dtpFechaRegistro;
        private System.Windows.Forms.TextBox txtPropietario;
        private System.Windows.Forms.ComboBox cmbEstatus;
        private System.Windows.Forms.ComboBox cmbColor;
        private System.Windows.Forms.ComboBox cmbMarca;
        private System.Windows.Forms.ComboBox cmbEstado;
        private System.Windows.Forms.TextBox txtMatricula;
        private System.Windows.Forms.Label label9;
        private System.Windows.Forms.Label label8;
        private System.Windows.Forms.Label label7;
        private System.Windows.Forms.Label label6;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.TextBox txtMatriculaActual;
        private System.Windows.Forms.TextBox txtFilenameActual;
        private System.Windows.Forms.Label label10;
        private System.Windows.Forms.TextBox txtPropietarioActual;
        private System.Windows.Forms.TextBox txtEstadoActual;
        private System.Windows.Forms.TextBox txtMarcaActual;
        private System.Windows.Forms.TextBox txtColorActual;
        private System.Windows.Forms.TextBox txtEstatusActual;
        private System.Windows.Forms.TextBox txtFechaActual;
        private System.Windows.Forms.PictureBox pictureBox1;
    }
}