from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Avg, F, Max
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
import pandas as pd
import json

from .models import Product
from .forms import ProductForm, ExcelImportForm

@login_required
def export_products_excel(request):
    """Export products to Excel"""
    search_query = request.GET.get('search', '')
    unit_filter = request.GET.get('unit', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(brand__icontains=search_query)
        )
    
    if unit_filter:
        products = products.filter(unit=unit_filter)
    
    data = []
    for product in products:
        data.append({
            'ID': product.id,
            'Nomi': product.name,
            'Brend': product.brand,
            'Kelgandagi narx (so\'m)': float(product.purchase_price),
            'Sotuvdagi narx (so\'m)': float(product.selling_price),
            'Miqdor': float(product.quantity),
            'O\'lchov birligi': product.get_unit_display(),
            'Yaratilgan sana': product.created_at.strftime('%d.%m.%Y %H:%M'),
            'Yangilangan sana': product.updated_at.strftime('%d.%m.%Y %H:%M')
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="mahsulotlar.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Mahsulotlar', index=False)
        worksheet = writer.sheets['Mahsulotlar']
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    return response

@login_required
def product_import(request):
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Check and map column names
                column_mapping = {
                    'Nomi': 'name',
                    'Brend': 'brand', 
                    'Kelgandagi narx (so\'m)': 'purchase_price',
                    'Kelgandagi narx': 'purchase_price',
                    'Sotuvdagi narx (so\'m)': 'selling_price',
                    'Sotuvdagi narx': 'selling_price',
                    'Narx (so\'m)': 'selling_price',  # Fallback for old format
                    'Narx': 'selling_price',
                    'Dona': 'quantity',
                    'Miqdor': 'quantity',
                    'O\'lchov birligi': 'unit',
                    'Oʻlchov birligi': 'unit',
                    'O‘lchov birligi': 'unit',
                }
                
                # Rename columns to standard names
                df = df.rename(columns=column_mapping)
                
                # Check required columns after mapping
                required_columns = ['name', 'brand', 'selling_price', 'quantity', 'unit']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    form.add_error('excel_file', f'Quyidagi ustunlar topilmadi: {", ".join(missing_columns)}')
                    return render(request, "products/productimport.html", {"form": form})
                
                # Process data
                products_data = []
                for index, row in df.iterrows():
                    # Skip empty rows or header-like rows
                    if pd.isna(row['name']) or pd.isna(row['brand']) or row['name'] == 'Nomi' or row['brand'] == 'Brend':
                        continue
                    
                    # Convert unit to lowercase and standardize
                    unit = str(row['unit']).strip().lower()
                    unit_mapping = {
                        'kg': 'kg',
                        'kilogramm': 'kg',
                        'dona': 'dona', 
                        'metr': 'metr',
                        'kub': 'kub',
                        'litr': 'litr'
                    }
                    unit = unit_mapping.get(unit, 'dona')  # default to 'dona'
                    
                    purchase_price = float(row.get('purchase_price', row.get('selling_price', 0)))
                    selling_price = float(row['selling_price'])
                    
                    product_data = {
                        'index': index + 2,  # Excel row number (starting from 2 for header)
                        'name': str(row['name']).strip(),
                        'brand': str(row['brand']).strip(),
                        'purchase_price': purchase_price,
                        'selling_price': selling_price,
                        'quantity': float(row['quantity']),
                        'unit': unit,
                        'existing_product': None,
                        'action': 'create'  # default action
                    }
                    
                    # Check for existing product
                    try:
                        existing_product = Product.objects.get(
                            Q(name__iexact=product_data['name']) & 
                            Q(brand__iexact=product_data['brand'])
                        )
                        product_data['existing_product'] = {
                            'id': existing_product.id,
                            'name': existing_product.name,
                            'brand': existing_product.brand,
                            'purchase_price': float(existing_product.purchase_price),
                            'selling_price': float(existing_product.selling_price),
                            'quantity': float(existing_product.quantity),
                            'unit': existing_product.unit
                        }
                        product_data['action'] = 'update'
                    except Product.DoesNotExist:
                        pass
                    
                    products_data.append(product_data)
                
                # Store in session for processing
                request.session['import_data'] = json.dumps(products_data, default=str)
                
                return render(request, "products/productimport_preview.html", {
                    "products_data": products_data,
                    "total_products": len(products_data),
                    "new_products": len([p for p in products_data if p['action'] == 'create']),
                    "update_products": len([p for p in products_data if p['action'] == 'update'])
                })
                
            except Exception as e:
                form.add_error('excel_file', f'Excel faylni o\'qishda xatolik: {str(e)}')
    else:
        form = ExcelImportForm()
    
    return render(request, "products/productimport.html", {"form": form})

@login_required
def product_list(request):
    # Search functionality
    search_query = request.GET.get('search', '')
    
    # Filter by unit
    unit_filter = request.GET.get('unit', '')
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'id')
    sort_order = request.GET.get('order', 'asc')
    
    # Stock level filter
    stock_filter = request.GET.get('stock', '')
    
    # Start with all products
    products = Product.objects.all()
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(brand__icontains=search_query)
        )
    
    # Apply unit filter
    if unit_filter:
        products = products.filter(unit=unit_filter)
    
    if sort_by in ['id', 'name', 'brand', 'selling_price', 'quantity', 'created_at']:
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        products = products.order_by(sort_by)
    else:
        products = products.order_by('id')
    
    # Get statistics
    total_products = products.count()
    
    # Convert Decimal to float safely
    try:
        total_quantity_result = products.aggregate(total=Sum('quantity'))['total']
        total_quantity = float(total_quantity_result) if total_quantity_result else 0.0
    except (TypeError, ValueError):
        total_quantity = 0.0
    
    try:
        total_value_result = products.aggregate(
            total=Sum(F('selling_price') * F('quantity'))
        )['total']
        total_value = float(total_value_result) if total_value_result else 0.0
    except (TypeError, ValueError):
        total_value = 0.0
    
    # Stock level statistics - simplified
    try:
        avg_quantity_result = products.aggregate(avg=Avg('quantity'))['avg']
        avg_quantity = float(avg_quantity_result) if avg_quantity_result else 0.0
    except (TypeError, ValueError):
        avg_quantity = 0.0
    
    # Simple stock level calculation
    low_stock = 0
    medium_stock = 0
    high_stock = 0
    
    if avg_quantity > 0:
        for product in products:
            product_qty = float(product.quantity)
            if product_qty < avg_quantity * 0.1:
                low_stock += 1
            elif product_qty < avg_quantity * 0.5:
                medium_stock += 1
            else:
                high_stock += 1
    
    # Apply stock level filter after calculations
    if stock_filter and avg_quantity > 0:
        filtered_products = []
        for product in products:
            product_qty = float(product.quantity)
            if stock_filter == 'low' and product_qty < avg_quantity * 0.1:
                filtered_products.append(product)
            elif stock_filter == 'medium' and product_qty >= avg_quantity * 0.1 and product_qty < avg_quantity * 0.5:
                filtered_products.append(product)
            elif stock_filter == 'high' and product_qty >= avg_quantity * 0.5:
                filtered_products.append(product)
        
        # Convert back to queryset if needed, or use the filtered list
        from django.db.models.expressions import Case, When, Value
        from django.db.models import IntegerField
        
        if filtered_products:
            product_ids = [p.id for p in filtered_products]
            preserved_order = Case(
                *[When(id=id, then=Value(pos)) for pos, id in enumerate(product_ids)],
                output_field=IntegerField()
            )
            products = products.filter(id__in=product_ids).order_by(preserved_order)
        else:
            products = products.none()
    
    # Get unique units for filter
    units = Product.objects.values_list('unit', flat=True).distinct()
    
    context = {
        'products': products,
        'search_query': search_query,
        'unit_filter': unit_filter,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'stock_filter': stock_filter,
        'units': units,
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_value': total_value,
        'avg_quantity': avg_quantity,
        'low_stock': low_stock,
        'medium_stock': medium_stock,
        'high_stock': high_stock,
    }
    
    return render(request, "products/productlist.html", context)

@login_required
def statistics_view(request):
    try:
        # Base query—adapt for filters if needed (e.g., date ranges via GET)
        base_query = Product.objects.all()
        total_products = base_query.count()
        
        if total_products == 0:
            context = {
                'total_products': 0,
                'total_value': Decimal('0'),
                'avg_price': Decimal('0'),
                'avg_quantity': Decimal('0'),
                'low_stock_count': 0,
                'low_stock_percentage': Decimal('0'),
                'high_value_count': 0,
                'high_value_percentage': Decimal('0'),
                'growth_products': 0,
                'high_value_threshold': Decimal('0'),
                'last_updated': timezone.now(),
            }
            return render(request, "statistic/statistic.html", context)
        
        avg_price_raw = base_query.aggregate(avg=Avg('selling_price'))['avg']
        avg_price = Decimal(str(avg_price_raw)) if avg_price_raw is not None else Decimal('0')
        avg_quantity_raw = base_query.aggregate(avg=Avg('quantity'))['avg']
        avg_quantity = Decimal(str(avg_quantity_raw)) if avg_quantity_raw is not None else Decimal('0')
        
        # Total value: Sum(F('selling_price') * F('quantity'))
        total_value_raw = base_query.aggregate(total=Sum(F('selling_price') * F('quantity')))['total']
        total_value = total_value_raw if total_value_raw is not None else Decimal('0')
        
        # Low stock: Threshold as avg_quantity / Decimal('2')
        low_threshold = avg_quantity / Decimal('2') if avg_quantity > 0 else Decimal('10')
        low_stock_query = base_query.filter(quantity__lt=low_threshold)
        low_stock_count = low_stock_query.count()
        low_stock_percentage = (Decimal(str(low_stock_count)) / Decimal(str(total_products)) * Decimal('100')) if total_products > 0 else Decimal('0')
        
        # High value: Items > avg_price * Decimal('1.5')
        high_threshold = avg_price * Decimal('1.5') if avg_price > 0 else Decimal('10000')
        high_value_query = base_query.filter(selling_price__gt=high_threshold)
        high_value_count = high_value_query.count()
        high_value_percentage = (Decimal(str(high_value_count)) / Decimal(str(total_products)) * Decimal('100')) if total_products > 0 else Decimal('0')
        
        # Growth: Products added last month vs previous
        last_month_start = timezone.now().date() - timedelta(days=30)
        prev_month_start = last_month_start - timedelta(days=30)
        last_month_count = base_query.filter(created_at__date__gte=last_month_start).count()
        prev_month_count = base_query.filter(created_at__date__gte=prev_month_start, created_at__date__lt=last_month_start).count()
        growth_products = last_month_count - prev_month_count
        
        # Last updated
        last_updated_raw = base_query.aggregate(max_updated=Max('updated_at'))['max_updated']
        last_updated = last_updated_raw if last_updated_raw else timezone.now()
        
        context = {
            'total_products': total_products,
            'total_value': total_value,
            'avg_price': avg_price,
            'avg_quantity': avg_quantity,
            'low_stock_count': low_stock_count,
            'low_stock_percentage': low_stock_percentage,
            'high_value_count': high_value_count,
            'high_value_percentage': high_value_percentage,
            'growth_products': growth_products,
            'high_value_threshold': high_threshold,
            'last_updated': last_updated,
        }
        
    except Exception as e:
        print(f"[v0] Stats view error: {e}")
        context = {
            'total_products': 0,
            'total_value': Decimal('0'),
            'avg_price': Decimal('0'),
            'avg_quantity': Decimal('0'),
            'low_stock_count': 0,
            'low_stock_percentage': Decimal('0'),
            'high_value_count': 0,
            'high_value_percentage': Decimal('0'),
            'growth_products': 0,
            'high_value_threshold': Decimal('0'),
            'last_updated': timezone.now(),
        }
    
    return render(request, "statistic/statistic.html", context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            brand = form.cleaned_data['brand'].strip()
            
            # Check if user forced creation
            if request.POST.get('force_create'):
                try:
                    form.save()
                    return redirect('productlist')
                except IntegrityError:
                    form.add_error(None, "Bu mahsulot allaqachon mavjud")
            else:
                # Check for existing product (case-insensitive)
                try:
                    duplicate_product = Product.objects.get(
                        Q(name__iexact=name) & Q(brand__iexact=brand)
                    )
                    
                    # If product exists, show confirmation modal
                    return render(request, "products/productform.html", {
                        "form": form,
                        "title": "Yangi mahsulot yaratish",
                        "action": "productcreate",
                        "duplicate_product": duplicate_product,
                        "show_modal": True
                    })
                    
                except Product.DoesNotExist:
                    # No duplicate found, save normally
                    try:
                        form.save()
                        return redirect('productlist')
                    except IntegrityError:
                        form.add_error(None, "Bu mahsulot allaqachon mavjud")
    else:
        form = ProductForm()
    
    return render(request, "products/productform.html", {
        "form": form,
        "title": "Yangi mahsulot yaratish",
        "action": "productcreate",
        "duplicate_product": None,
        "show_modal": False
    })

@login_required
@csrf_exempt
def check_existing_product(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            brand = data.get('brand', '').strip()
            
            if name and brand:
                try:
                    # Case-insensitive search
                    existing_product = Product.objects.get(
                        Q(name__iexact=name) & Q(brand__iexact=brand)
                    )
                    return JsonResponse({
                        'exists': True,
                        'product_id': existing_product.id,
                        'name': existing_product.name,
                        'brand': existing_product.brand,
                        'purchase_price': str(existing_product.purchase_price),
                        'selling_price': str(existing_product.selling_price),
                        'quantity': str(existing_product.quantity),
                        'unit': existing_product.unit
                    })
                except Product.DoesNotExist:
                    return JsonResponse({'exists': False})
            else:
                return JsonResponse({'exists': False})
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'})
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
@csrf_exempt
def update_existing_product(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            new_purchase_price = data.get('purchase_price')
            new_selling_price = data.get('selling_price')
            new_quantity = data.get('quantity')
            new_unit = data.get('unit')
            
            if not all([product_id, new_selling_price, new_quantity, new_unit]):
                return JsonResponse({'success': False, 'error': 'Barcha maydonlarni to\'ldiring'})
            
            try:
                product = Product.objects.get(id=product_id)
                
                if new_purchase_price:
                    product.purchase_price = new_purchase_price
                product.selling_price = new_selling_price
                product.quantity = float(product.quantity) + float(new_quantity)  # Add to existing quantity
                product.unit = new_unit
                product.save()
                
                return JsonResponse({'success': True, 'message': 'Mahsulot muvaffaqiyatli yangilandi'})
                
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Mahsulot topilmadi'})
            except ValueError as e:
                return JsonResponse({'success': False, 'error': f'Noto\'g\'ri qiymat: {str(e)}'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Xatolik: {str(e)}'})
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'error': f'Server xatosi: {str(e)}'})
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
def product_view(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, "products/productview.html", {"product": product})

@login_required
def product_edit(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('productlist')
    else:
        form = ProductForm(instance=product)
    
    return render(request, "products/productform.html", {
        "form": form,
        "title": "Mahsulotni tahrirlash",
        "action": "productedit",
        "product": product,
        "duplicate_product": None,
        "show_modal": False
    })

@login_required
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        product.delete()
        return redirect('productlist')
    
    return render(request, "products/productdelete.html", {"product": product})

@login_required
@csrf_exempt
def process_import(request):
    if request.method == 'POST':
        try:
            print("[v0] Starting import process")
            import_data_json = request.session.get('import_data')
            if not import_data_json:
                print("[v0] No import data found in session")
                return JsonResponse({'success': False, 'error': 'Import ma\'lumotlari topilmadi'})
            
            products_data = json.loads(import_data_json)
            print(f"[v0] Processing {len(products_data)} products")
            
            results = {
                'created': 0,
                'updated': 0,
                'errors': 0,
                'error_messages': []
            }
            
            for product_data in products_data:
                try:
                    print(f"[v0] Processing: {product_data['name']} - Action: {product_data['action']}")
                    
                    purchase_price = Decimal(str(product_data['purchase_price']))
                    selling_price = Decimal(str(product_data['selling_price']))
                    quantity = Decimal(str(product_data['quantity']))
                    
                    if product_data['action'] == 'update' and product_data['existing_product']:
                        product = Product.objects.get(id=product_data['existing_product']['id'])
                        product.purchase_price = purchase_price
                        product.selling_price = selling_price
                        product.quantity = product.quantity + quantity
                        product.unit = product_data['unit']
                        product.save()
                        results['updated'] += 1
                        print(f"[v0] Updated: {product.name}")
                        
                    elif product_data['action'] == 'create':
                        product = Product.objects.create(
                            name=product_data['name'],
                            brand=product_data['brand'],
                            purchase_price=purchase_price,
                            selling_price=selling_price,
                            quantity=quantity,
                            unit=product_data['unit']
                        )
                        results['created'] += 1
                        print(f"[v0] Created: {product.name}")
                        
                except Exception as e:
                    results['errors'] += 1
                    error_msg = f"Qator {product_data['index']}: {product_data['name']} - {str(e)}"
                    results['error_messages'].append(error_msg)
                    print(f"[v0] Error: {error_msg}")
            
            # Clear session data
            if 'import_data' in request.session:
                del request.session['import_data']
            
            print(f"[v0] Import complete: {results['created']} created, {results['updated']} updated, {results['errors']} errors")
            
            return JsonResponse({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            print(f"[v0] Import process error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_product_info(request):
    """Get product information for sale form"""
    product_id = request.GET.get('product_id')
    
    if not product_id:
        return JsonResponse({'error': 'Product ID required'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'brand': product.brand,
            'purchase_price': float(product.purchase_price),
            'selling_price': float(product.selling_price),
            'quantity': float(product.quantity),
            'unit': product.unit
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
