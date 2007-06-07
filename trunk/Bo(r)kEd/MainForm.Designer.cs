/*
 * Created by SharpDevelop.
 * User: Spikeman
 * Date: 3/17/2007
 */
namespace Borked
{
	partial class MainForm
	{
		/// <summary>
		/// Designer variable used to keep track of non-visual components.
		/// </summary>
		private System.ComponentModel.IContainer components = null;
		
		/// <summary>
		/// Disposes resources used by the form.
		/// </summary>
		/// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
		protected override void Dispose(bool disposing)
		{
			if (disposing) {
				if (components != null) {
					components.Dispose();
				}
			}
			base.Dispose(disposing);
		}
		
		/// <summary>
		/// This method is required for Windows Forms designer support.
		/// Do not change the method contents inside the source code editor. The Forms designer might
		/// not be able to load this method if it was changed manually.
		/// </summary>
		private void InitializeComponent()
		{
			this.bLoadTable = new System.Windows.Forms.Button();
			this.tDump = new System.Windows.Forms.TextBox();
			this.openTable = new System.Windows.Forms.OpenFileDialog();
			this.openROM = new System.Windows.Forms.OpenFileDialog();
			this.bLoadROM = new System.Windows.Forms.Button();
			this.bDump = new System.Windows.Forms.Button();
			this.statusStrip = new System.Windows.Forms.StatusStrip();
			this.saveDump = new System.Windows.Forms.SaveFileDialog();
			this.prog = new System.Windows.Forms.ToolStripStatusLabel();
			this.toolStripStatusLabel2 = new System.Windows.Forms.ToolStripStatusLabel();
			this.statusStrip.SuspendLayout();
			this.SuspendLayout();
			// 
			// bLoadTable
			// 
			this.bLoadTable.Location = new System.Drawing.Point(12, 212);
			this.bLoadTable.Name = "bLoadTable";
			this.bLoadTable.Size = new System.Drawing.Size(75, 23);
			this.bLoadTable.TabIndex = 0;
			this.bLoadTable.Text = "Load Table";
			this.bLoadTable.UseVisualStyleBackColor = true;
			this.bLoadTable.Click += new System.EventHandler(this.BLoadTableClick);
			// 
			// tDump
			// 
			this.tDump.Font = new System.Drawing.Font("MingLiU", 9.75F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
			this.tDump.Location = new System.Drawing.Point(12, 12);
			this.tDump.Multiline = true;
			this.tDump.Name = "tDump";
			this.tDump.Size = new System.Drawing.Size(268, 194);
			this.tDump.TabIndex = 1;
			// 
			// openTable
			// 
			this.openTable.Filter = "Table Files|*.tbl|All Files|*.*";
			// 
			// openROM
			// 
			this.openROM.Filter = "GBA ROMs|*.gba|All Files|*.*";
			// 
			// bLoadROM
			// 
			this.bLoadROM.Location = new System.Drawing.Point(93, 212);
			this.bLoadROM.Name = "bLoadROM";
			this.bLoadROM.Size = new System.Drawing.Size(75, 23);
			this.bLoadROM.TabIndex = 2;
			this.bLoadROM.Text = "Load ROM";
			this.bLoadROM.UseVisualStyleBackColor = true;
			this.bLoadROM.Click += new System.EventHandler(this.BLoadROMClick);
			// 
			// bDump
			// 
			this.bDump.Location = new System.Drawing.Point(174, 212);
			this.bDump.Name = "bDump";
			this.bDump.Size = new System.Drawing.Size(75, 23);
			this.bDump.TabIndex = 3;
			this.bDump.Text = "Dump";
			this.bDump.UseVisualStyleBackColor = true;
			this.bDump.Click += new System.EventHandler(this.BDumpClick);
			// 
			// statusStrip
			// 
			this.statusStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
									this.prog,
									this.toolStripStatusLabel2});
			this.statusStrip.Location = new System.Drawing.Point(0, 243);
			this.statusStrip.Name = "statusStrip";
			this.statusStrip.Size = new System.Drawing.Size(292, 22);
			this.statusStrip.TabIndex = 6;
			// 
			// saveDump
			// 
			this.saveDump.Filter = "SJS Files|*.sjs|All Files|*.*";
			// 
			// prog
			// 
			this.prog.Name = "prog";
			this.prog.Size = new System.Drawing.Size(13, 17);
			this.prog.Text = "0";
			// 
			// toolStripStatusLabel2
			// 
			this.toolStripStatusLabel2.Name = "toolStripStatusLabel2";
			this.toolStripStatusLabel2.Size = new System.Drawing.Size(35, 17);
			this.toolStripStatusLabel2.Text = "/9976";
			// 
			// MainForm
			// 
			this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
			this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
			this.ClientSize = new System.Drawing.Size(292, 265);
			this.Controls.Add(this.statusStrip);
			this.Controls.Add(this.bDump);
			this.Controls.Add(this.bLoadROM);
			this.Controls.Add(this.tDump);
			this.Controls.Add(this.bLoadTable);
			this.Name = "MainForm";
			this.Text = "Bo(r)kEd";
			this.statusStrip.ResumeLayout(false);
			this.statusStrip.PerformLayout();
			this.ResumeLayout(false);
			this.PerformLayout();
		}
		private System.Windows.Forms.ToolStripStatusLabel toolStripStatusLabel2;
		private System.Windows.Forms.ToolStripStatusLabel prog;
		private System.Windows.Forms.SaveFileDialog saveDump;
		private System.Windows.Forms.StatusStrip statusStrip;
		private System.Windows.Forms.Button bDump;
		private System.Windows.Forms.Button bLoadROM;
		private System.Windows.Forms.OpenFileDialog openROM;
		private System.Windows.Forms.OpenFileDialog openTable;
		private System.Windows.Forms.TextBox tDump;
		private System.Windows.Forms.Button bLoadTable;
	}
}
