namespace MLP_Register
{
    partial class Form1
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
            this.components = new System.ComponentModel.Container();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Form1));
            this.dataGridView1 = new System.Windows.Forms.DataGridView();
            this.btnAddRegister = new System.Windows.Forms.Button();
            this.imageList1 = new System.Windows.Forms.ImageList(this.components);
            this.btnUpdateRegister = new System.Windows.Forms.Button();
            this.btnDeleteRegister = new System.Windows.Forms.Button();
            this.btnLoadDB = new System.Windows.Forms.Button();
            this.btnClearData = new System.Windows.Forms.Button();
            this.openFileDialog1 = new System.Windows.Forms.OpenFileDialog();
            this.btnBuscarRegistro = new System.Windows.Forms.Button();
            this.pictureBox1 = new System.Windows.Forms.PictureBox();
            this.pictureBox2 = new System.Windows.Forms.PictureBox();
            this.lblLinkGitHub = new System.Windows.Forms.LinkLabel();
            this.label1 = new System.Windows.Forms.Label();
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView1)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox2)).BeginInit();
            this.SuspendLayout();
            // 
            // dataGridView1
            // 
            this.dataGridView1.BackgroundColor = System.Drawing.SystemColors.ButtonFace;
            this.dataGridView1.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dataGridView1.Dock = System.Windows.Forms.DockStyle.Right;
            this.dataGridView1.Location = new System.Drawing.Point(145, 0);
            this.dataGridView1.Name = "dataGridView1";
            this.dataGridView1.Size = new System.Drawing.Size(655, 500);
            this.dataGridView1.TabIndex = 0;
            this.dataGridView1.CellContentClick += new System.Windows.Forms.DataGridViewCellEventHandler(this.dataGridView1_CellContentClick);
            // 
            // btnAddRegister
            // 
            this.btnAddRegister.BackColor = System.Drawing.Color.DarkSlateBlue;
            this.btnAddRegister.BackgroundImageLayout = System.Windows.Forms.ImageLayout.None;
            this.btnAddRegister.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnAddRegister.FlatAppearance.BorderSize = 0;
            this.btnAddRegister.FlatAppearance.MouseOverBackColor = System.Drawing.Color.SlateBlue;
            this.btnAddRegister.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnAddRegister.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnAddRegister.ForeColor = System.Drawing.Color.White;
            this.btnAddRegister.Location = new System.Drawing.Point(-6, 86);
            this.btnAddRegister.Name = "btnAddRegister";
            this.btnAddRegister.Size = new System.Drawing.Size(152, 56);
            this.btnAddRegister.TabIndex = 1;
            this.btnAddRegister.Text = "Agregar registro";
            this.btnAddRegister.UseVisualStyleBackColor = false;
            this.btnAddRegister.Click += new System.EventHandler(this.btnAddRegister_Click);
            // 
            // imageList1
            // 
            this.imageList1.ColorDepth = System.Windows.Forms.ColorDepth.Depth8Bit;
            this.imageList1.ImageSize = new System.Drawing.Size(16, 16);
            this.imageList1.TransparentColor = System.Drawing.Color.Transparent;
            // 
            // btnUpdateRegister
            // 
            this.btnUpdateRegister.BackColor = System.Drawing.Color.DarkSlateBlue;
            this.btnUpdateRegister.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnUpdateRegister.FlatAppearance.BorderSize = 0;
            this.btnUpdateRegister.FlatAppearance.MouseOverBackColor = System.Drawing.Color.SlateBlue;
            this.btnUpdateRegister.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnUpdateRegister.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnUpdateRegister.ForeColor = System.Drawing.Color.White;
            this.btnUpdateRegister.Location = new System.Drawing.Point(-6, 155);
            this.btnUpdateRegister.Name = "btnUpdateRegister";
            this.btnUpdateRegister.Size = new System.Drawing.Size(152, 56);
            this.btnUpdateRegister.TabIndex = 2;
            this.btnUpdateRegister.Text = "Actualizar registro";
            this.btnUpdateRegister.UseVisualStyleBackColor = false;
            this.btnUpdateRegister.Click += new System.EventHandler(this.btnUpdateRegister_Click);
            // 
            // btnDeleteRegister
            // 
            this.btnDeleteRegister.BackColor = System.Drawing.Color.DarkSlateBlue;
            this.btnDeleteRegister.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnDeleteRegister.FlatAppearance.BorderSize = 0;
            this.btnDeleteRegister.FlatAppearance.MouseOverBackColor = System.Drawing.Color.SlateBlue;
            this.btnDeleteRegister.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnDeleteRegister.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnDeleteRegister.ForeColor = System.Drawing.Color.White;
            this.btnDeleteRegister.Location = new System.Drawing.Point(-6, 224);
            this.btnDeleteRegister.Name = "btnDeleteRegister";
            this.btnDeleteRegister.Size = new System.Drawing.Size(152, 56);
            this.btnDeleteRegister.TabIndex = 3;
            this.btnDeleteRegister.Text = "Eliminar registro";
            this.btnDeleteRegister.UseVisualStyleBackColor = false;
            this.btnDeleteRegister.Click += new System.EventHandler(this.btnDeleteRegister_Click);
            // 
            // btnLoadDB
            // 
            this.btnLoadDB.BackColor = System.Drawing.Color.DarkSlateBlue;
            this.btnLoadDB.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnLoadDB.FlatAppearance.BorderSize = 0;
            this.btnLoadDB.FlatAppearance.MouseOverBackColor = System.Drawing.Color.SlateBlue;
            this.btnLoadDB.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnLoadDB.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnLoadDB.ForeColor = System.Drawing.Color.White;
            this.btnLoadDB.Location = new System.Drawing.Point(-6, 293);
            this.btnLoadDB.Name = "btnLoadDB";
            this.btnLoadDB.Size = new System.Drawing.Size(152, 56);
            this.btnLoadDB.TabIndex = 4;
            this.btnLoadDB.Text = "Cargar datos";
            this.btnLoadDB.UseVisualStyleBackColor = false;
            this.btnLoadDB.Click += new System.EventHandler(this.btnLoadDB_Click);
            // 
            // btnClearData
            // 
            this.btnClearData.BackColor = System.Drawing.Color.DarkSlateBlue;
            this.btnClearData.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnClearData.FlatAppearance.BorderSize = 0;
            this.btnClearData.FlatAppearance.MouseOverBackColor = System.Drawing.Color.SlateBlue;
            this.btnClearData.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnClearData.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnClearData.ForeColor = System.Drawing.Color.White;
            this.btnClearData.Location = new System.Drawing.Point(-6, 362);
            this.btnClearData.Name = "btnClearData";
            this.btnClearData.Size = new System.Drawing.Size(152, 56);
            this.btnClearData.TabIndex = 5;
            this.btnClearData.Text = "Limpiar datos";
            this.btnClearData.UseVisualStyleBackColor = false;
            this.btnClearData.Click += new System.EventHandler(this.btnClearData_Click);
            // 
            // openFileDialog1
            // 
            this.openFileDialog1.FileName = "MLPR.db";
            this.openFileDialog1.Filter = "Archivos SQLite (*.db;*.sqlite;*.sqlite3)|*.db;*.sqlite;*.sqlite3|Todos los archi" +
    "vos (*.*)|*.*";
            this.openFileDialog1.InitialDirectory = "Environment.SpecialFolder.Documents";
            this.openFileDialog1.Title = "Selecciona tu archivo de base de datos";
            // 
            // btnBuscarRegistro
            // 
            this.btnBuscarRegistro.BackColor = System.Drawing.Color.DarkSlateBlue;
            this.btnBuscarRegistro.BackgroundImageLayout = System.Windows.Forms.ImageLayout.None;
            this.btnBuscarRegistro.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnBuscarRegistro.FlatAppearance.BorderSize = 0;
            this.btnBuscarRegistro.FlatAppearance.MouseOverBackColor = System.Drawing.Color.SlateBlue;
            this.btnBuscarRegistro.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnBuscarRegistro.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnBuscarRegistro.ForeColor = System.Drawing.Color.White;
            this.btnBuscarRegistro.Location = new System.Drawing.Point(-6, 17);
            this.btnBuscarRegistro.Name = "btnBuscarRegistro";
            this.btnBuscarRegistro.Size = new System.Drawing.Size(152, 56);
            this.btnBuscarRegistro.TabIndex = 6;
            this.btnBuscarRegistro.Text = "Buscar matricula";
            this.btnBuscarRegistro.UseVisualStyleBackColor = false;
            this.btnBuscarRegistro.Click += new System.EventHandler(this.btnBuscarRegistro_Click);
            // 
            // pictureBox1
            // 
            this.pictureBox1.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("pictureBox1.BackgroundImage")));
            this.pictureBox1.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Stretch;
            this.pictureBox1.Location = new System.Drawing.Point(4, 424);
            this.pictureBox1.Name = "pictureBox1";
            this.pictureBox1.Size = new System.Drawing.Size(67, 47);
            this.pictureBox1.TabIndex = 7;
            this.pictureBox1.TabStop = false;
            // 
            // pictureBox2
            // 
            this.pictureBox2.BackgroundImage = ((System.Drawing.Image)(resources.GetObject("pictureBox2.BackgroundImage")));
            this.pictureBox2.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Stretch;
            this.pictureBox2.Location = new System.Drawing.Point(75, 424);
            this.pictureBox2.Name = "pictureBox2";
            this.pictureBox2.Size = new System.Drawing.Size(69, 47);
            this.pictureBox2.TabIndex = 8;
            this.pictureBox2.TabStop = false;
            // 
            // lblLinkGitHub
            // 
            this.lblLinkGitHub.ActiveLinkColor = System.Drawing.Color.White;
            this.lblLinkGitHub.AutoSize = true;
            this.lblLinkGitHub.BackColor = System.Drawing.Color.Transparent;
            this.lblLinkGitHub.Font = new System.Drawing.Font("Microsoft Sans Serif", 6.5F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblLinkGitHub.ForeColor = System.Drawing.Color.White;
            this.lblLinkGitHub.LinkBehavior = System.Windows.Forms.LinkBehavior.AlwaysUnderline;
            this.lblLinkGitHub.LinkColor = System.Drawing.Color.White;
            this.lblLinkGitHub.Location = new System.Drawing.Point(65, 478);
            this.lblLinkGitHub.Name = "lblLinkGitHub";
            this.lblLinkGitHub.Size = new System.Drawing.Size(78, 12);
            this.lblLinkGitHub.TabIndex = 9;
            this.lblLinkGitHub.TabStop = true;
            this.lblLinkGitHub.Text = "@GustavoMurillo";
            this.lblLinkGitHub.VisitedLinkColor = System.Drawing.Color.FromArgb(((int)(((byte)(255)))), ((int)(((byte)(192)))), ((int)(((byte)(255)))));
            this.lblLinkGitHub.LinkClicked += new System.Windows.Forms.LinkLabelLinkClickedEventHandler(this.lblLinkGitHub_LinkClicked);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 6.5F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label1.ForeColor = System.Drawing.Color.White;
            this.label1.Location = new System.Drawing.Point(8, 479);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(59, 12);
            this.label1.TabIndex = 10;
            this.label1.Text = "LPR-Sentinel";
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.MidnightBlue;
            this.ClientSize = new System.Drawing.Size(800, 500);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.lblLinkGitHub);
            this.Controls.Add(this.pictureBox2);
            this.Controls.Add(this.pictureBox1);
            this.Controls.Add(this.btnBuscarRegistro);
            this.Controls.Add(this.btnClearData);
            this.Controls.Add(this.btnLoadDB);
            this.Controls.Add(this.btnDeleteRegister);
            this.Controls.Add(this.btnUpdateRegister);
            this.Controls.Add(this.btnAddRegister);
            this.Controls.Add(this.dataGridView1);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
            this.Name = "Form1";
            this.ShowIcon = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "MLP-Register";
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView1)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox1)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.pictureBox2)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.DataGridView dataGridView1;
        private System.Windows.Forms.Button btnAddRegister;
        private System.Windows.Forms.ImageList imageList1;
        private System.Windows.Forms.Button btnUpdateRegister;
        private System.Windows.Forms.Button btnDeleteRegister;
        private System.Windows.Forms.Button btnLoadDB;
        private System.Windows.Forms.Button btnClearData;
        private System.Windows.Forms.OpenFileDialog openFileDialog1;
        private System.Windows.Forms.Button btnBuscarRegistro;
        private System.Windows.Forms.PictureBox pictureBox1;
        private System.Windows.Forms.PictureBox pictureBox2;
        private System.Windows.Forms.LinkLabel lblLinkGitHub;
        private System.Windows.Forms.Label label1;
    }
}

