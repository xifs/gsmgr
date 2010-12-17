#encoding:utf8
import gtk,gtk.glade,gobject
import os,boto,tempfile
from boto.exception import BotoServerError

class GsGtk():
	#bucket = 'virtue'
	#list_status = 'object'
	bucket = ''
	list_status = 'bucket'
	def __init__(self):
		self.builder = gtk.Builder()
		#builder.set_translation_domain('gstorage')
		self.builder.add_from_file('gstorage.ui')
		self.builder.connect_signals(self)
		self.remote_treeview = self.builder.get_object('remote_treeview')
		self.remote_treeview_column = self.builder.get_object('remote_treeview_column')
		self.remote_liststore = self.builder.get_object('remote_liststore')
		self.properties = self.builder.get_object('properties')
		if self.bucket == '':
			self.remote_treeview_column.set_title('Buckets')
		else:
			self.remote_treeview_column.set_title('Objects')
		self.refresh(self)
	
	def new_bucket(self,widget):
		self.new_bucket_dialog = self.builder.get_object('new_bucket_dialog')
		self.entry1 = self.builder.get_object('entry1')
		response = self.new_bucket_dialog.run()
		if response == gtk.RESPONSE_OK:
			bucket_name = self.entry1.get_text()
			#len(bucket_name)
			print bucket_name
			try:
				bucket_uri = boto.storage_uri(bucket_name, 'gs')
				bucket_uri.create_bucket()
			except:
				print 'failed'
			#except BotoServerError.StorageCreateError.GSCreateError,e:
			#	print e
			self.refresh(self)
		self.new_bucket_dialog.hide()

	def refresh(self,widget):
		self.remote_liststore = self.builder.get_object('remote_liststore')
		print 'refresh list'
		self.remote_liststore.clear()
		#'''
		if self.bucket == '':
			self.list_status = 'bucket'
		else:
			self.list_status = 'object'
		uri = boto.storage_uri(self.bucket,'gs')
		if self.bucket <> '':
			buckets = uri.get_all_keys()
		else:
			buckets = uri.get_all_buckets()
		for bucket in buckets:
			self.remote_liststore.append([bucket.name])
		'''
		buckets = ['100','200']
		for bucket in buckets:
			self.remote_liststore.append([bucket])
		'''

	def upload(self,widget):
		if self.bucket == '':
			return 0
		choose_for_upload = gtk.FileChooserDialog(title='Upload ... '
			,parent=None
			,action=gtk.FILE_CHOOSER_ACTION_OPEN
			,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		response = choose_for_upload.run()
		if response == gtk.RESPONSE_OK:
			filename = choose_for_upload.get_uri()
			local_uri = boto.storage_uri(filename)
			remote_uri = boto.storage_uri('gs://' + self.bucket + os.sep + filename.split('/')[-1:][0])
			new_remote_uri = remote_uri.clone_replace_name(local_uri.object_name)
			remote_key = remote_uri.new_key()
			local_key = local_uri.get_key()
			tmp = tempfile.TemporaryFile()
			local_key.get_file(tmp)
			tmp.seek(0)
			remote_key.set_contents_from_file(tmp)
			self.refresh(self)
		choose_for_upload.hide()

	def download(self,widget):
		choose_for_download = gtk.FileChooserDialog(title='Download ... '
			,parent=None
			,action=gtk.FILE_CHOOSER_ACTION_SAVE
			,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		if self.remote_treeview.get_selection().count_selected_rows() == 0:
			print '請至少選擇一個文件'
			return 0
		row = self.remote_treeview.get_selection().get_selected_rows()[1][0]
		remote_name = self.remote_liststore[row][0]
		choose_for_download.set_current_name(remote_name.split('/')[-1:][0])
		response = choose_for_download.run()
		if response == gtk.RESPONSE_OK:
			filename = choose_for_download.get_uri()
			local_uri = boto.storage_uri(filename)
			remote_uri = boto.storage_uri('gs://' + self.bucket + os.sep + remote_name)
			new_local_uri = local_uri.clone_replace_name(remote_uri.object_name)
			remote_key = remote_uri.get_key()
			local_key = local_uri.new_key()
			tmp = tempfile.TemporaryFile()
			remote_key.get_file(tmp)
			tmp.seek(0)
			local_key.set_contents_from_file(tmp)
		choose_for_download.destroy()

	def delete(self,widget):
		if self.remote_treeview.get_selection().count_selected_rows() == 0:
			print '請至少選擇一個文件'
			return 0
		row = self.remote_treeview.get_selection().get_selected_rows()[1][0]
		remote_name = self.remote_liststore[row][0]
		print remote_name
		if self.list_status == 'bucket':
			remote_uri = boto.storage_uri(remote_name,'gs')
			remote_uri.delete_bucket()
			self.refresh(self)
		elif self.list_status == 'object':
			remote_uri = boto.storage_uri(self.bucket+os.sep+remote_name,'gs')
			remote_uri.delete_key()
			self.refresh(self)
			#	objs = remote_uri.get_bucket()
			#	if objs:
			#		for obj in objs:
			#			obj.delete()
			#remote_uri.delete_bucket()

	def get_properties(self,widget):
		if self.remote_treeview.get_selection().count_selected_rows() == 0:
			print '請至少選擇一個文件'
			return 0
		row = self.remote_treeview.get_selection().get_selected_rows()[1][0]
		remote_name = self.remote_liststore[row][0]
		print remote_name
		remote_uri = boto.storage_uri(self.bucket+os.sep+remote_name,'gs')
		remote_key = remote_uri.get_key()
		remote_info = remote_key.name + '\n' + str(remote_key.last_modified) + '\n' + str(remote_key.size) + '\n' + remote_key.content_type + '\n' + remote_uri.uri
		self.properties.set_markup(remote_info)
		print remote_key.name
		print remote_key.last_modified
		print remote_key.size
		print remote_key.content_type
		print remote_uri.uri
		self.properties.run()
		self.properties.hide()

	def on_click(self,widget,row,col):
		if self.list_status == 'bucket':
			row = self.remote_treeview.get_selection().get_selected_rows()[1][0]
			remote_name = self.remote_liststore[row][0]
			self.bucket = remote_name
			self.refresh(self)
			'''
			model = widget.get_model()
			print model
			print widget.get_selection().get_selected()[0][0]
			if os.path.isdir(self.current + '/' + model[row][0]):
				self.current = self.current + '/' + model[row][0]
				self.bucket = self.bucket + model[row][0]
			self.store.clear()
			self.fill_store()
			'''
		elif self.list_status == 'object':
			print '確認要下載？'
			#self.download()

	def do_quit(self,widget):
		#self.config.write(open(configfile,'w'))
		gtk.main_quit()

if __name__ == '__main__':
	GsGtk()
	gtk.main()